"""
StadiumSense Backend - FastAPI + WebSocket

Accessibility copilot for FIFA World Cup 2026 fans.
Converts live stadium announcements into real-time captions,
translations, and haptic alerts for deaf/hard-of-hearing fans.
"""
import asyncio
import json
import os
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Optional, Dict, List
from dotenv import load_dotenv

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, APIRouter, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from anthropic import Anthropic
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

# Load environment
load_dotenv()

app = FastAPI(title="StadiumSense API", version="1.0.0")  # lifespan attached below after definition
api_router = APIRouter(prefix="/api")

# CORS setup: Restrict to localhost and default dev configurations securely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:8000"],  # Restricted for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# =====================
# Data Models with constraints
# =====================

class Announcement(BaseModel):
    id: str
    timestamp: float
    type: str
    original: str
    category: str
    severity: str
    plain_language: Optional[str] = None
    translated: Optional[dict] = None
    needs_avatar: bool = False
    icon: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    # Match event fields
    team_a: Optional[str] = None
    team_b: Optional[str] = None
    score_a: Optional[int] = None
    score_b: Optional[int] = None
    minute: Optional[int] = None
    scorer: Optional[str] = None

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=250)
    language: str = Field("en", min_length=2, max_length=5)
    location: Optional[str] = Field(None, max_length=50)

class RouteRequest(BaseModel):
    start: str = Field(..., min_length=3, max_length=50)
    destination: str = Field(..., min_length=3, max_length=50)
    step_free: bool = True

class BroadcastRequest(BaseModel):
    message: str = Field(..., min_length=5, max_length=500)
    category: str = Field("wayfinding", max_length=50)
    severity: str = Field("info", max_length=20)

class RequestHelp(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)
    location: str = Field(..., min_length=3, max_length=50)
    severity: str = Field("warning", max_length=20)

# =====================
# Rate Limiting
# =====================

class InMemoryRateLimiter:
    def __init__(self, requests_limit: int, window_seconds: int):
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        self.requests[client_id] = [t for t in self.requests[client_id] if now - t < self.window_seconds]
        if len(self.requests[client_id]) < self.requests_limit:
            self.requests[client_id].append(now)
            return True
        return False

ask_limiter = InMemoryRateLimiter(requests_limit=10, window_seconds=60)
route_limiter = InMemoryRateLimiter(requests_limit=15, window_seconds=60)
help_limiter = InMemoryRateLimiter(requests_limit=5, window_seconds=60)

async def check_ask_rate_limit(request: Request):
    """Dependency: enforce per-IP rate limit on the /ask endpoint."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not ask_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many questions. Please wait a moment.")

async def check_route_rate_limit(request: Request):
    """Dependency: enforce per-IP rate limit on the /route endpoint."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not route_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many routing requests. Please wait a moment.")

async def check_help_rate_limit(request: Request):
    """Dependency: enforce per-IP rate limit on the /request-help endpoint."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not help_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Too many help requests. Please wait a moment.")


# =====================
# Global State
# =====================

# Connected WebSocket clients: {section: [websocket]}
connected_clients: dict[str, list[WebSocket]] = {}

# Store processed announcements
announcements: list[dict] = []

# Store help requests
help_requests: list[dict] = []

# Load data files
def load_json(filename: str) -> dict:
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)

def load_text(filename: str) -> str:
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return f.read()

TIMELINE = load_json("match_timeline.json")
GRAPH = load_json("graph.json")
STADIUM_KB = load_text("stadium_kb.md")

# Simple vector store (will be initialized on startup)
kb_index: Optional[faiss.IndexFlatL2] = None
kb_chunks: list[str] = []
kb_embeddings: Optional[np.ndarray] = None
embedding_model = None

# =====================
# Initialize
# =====================

async def _init_vector_store():
    """Initialize the FAISS knowledge base vector store on app startup."""
    global kb_index, kb_chunks, kb_embeddings, embedding_model

    # Split KB into chunks by sections
    kb_text = STADIUM_KB
    kb_chunks = []
    current_chunk: list[str] = []

    for line in kb_text.split('\n'):
        if line.startswith('## ') or line.startswith('**'):
            if current_chunk:
                kb_chunks.append('\n'.join(current_chunk))
                current_chunk = []
        current_chunk.append(line)

    if current_chunk:
        kb_chunks.append('\n'.join(current_chunk))

    # Initialize embeddings
    try:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = embedding_model.encode(kb_chunks)
        kb_embeddings = np.array(embeddings).astype('float32')

        # Create FAISS index
        dim = embeddings.shape[1]
        kb_index = faiss.IndexFlatL2(dim)
        kb_index.add(kb_embeddings)
        print(f"Vector store initialized with {len(kb_chunks)} chunks")
    except Exception as e:
        print(f"Warning: Could not initialize vector store: {e}")
        kb_index = None

@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """FastAPI lifespan: initialize resources on startup, clean up on shutdown."""
    await _init_vector_store()
    yield
    # Shutdown: nothing to clean up currently

# Attach lifespan to app
app.router.lifespan_context = lifespan

# =====================
# WebSocket Hub
# =====================

async def broadcast_to_fans(announcement: dict):
    """Broadcast an announcement to all connected WebSocket fan devices."""
    # Get all sections
    all_sections = list(connected_clients.keys())
    if "all" in connected_clients:
        all_sections.append("all")

    for section in all_sections:
        dead_sockets = []
        for ws in connected_clients.get(section, []):
            try:
                await ws.send_json({
                    "type": "announcement",
                    "data": announcement
                })
            except Exception as e:
                print(f"Error broadcasting to a client, removing socket. Error: {e}")
                dead_sockets.append(ws)
        
        # Clean up dead sockets
        for ws in dead_sockets:
            if ws in connected_clients[section]:
                connected_clients[section].remove(ws)

@app.websocket("/ws/{section}/{language}")
async def websocket_endpoint(websocket: WebSocket, section: str, language: str):
    """WebSocket endpoint: fan devices connect here to receive live accessibility announcements."""
    await websocket.accept()

    # Add to connections
    if section not in connected_clients:
        connected_clients[section] = []
    connected_clients[section].append(websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "welcome",
            "message": f"Connected to StadiumSense - Section {section}, Language: {language}",
            "language": language
        })

        # Send recent announcements
        for ann in announcements[-10:]:
            await websocket.send_json({
                "type": "announcement",
                "data": ann
            })

        # Keep connection alive
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=30)
                # Handle ping/pong or other client messages
                if data.get("type") == "ping":
                    try:
                        await websocket.send_json({"type": "pong"})
                    except Exception:
                        break
            except asyncio.TimeoutError:
                # Send keep-alive ping
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if section in connected_clients and websocket in connected_clients[section]:
            connected_clients[section].remove(websocket)

# =====================
# Pipeline A: Announcement Transform
# =====================

def get_icon_for_category(category: str, severity: str) -> str:
    """Map category to icon."""
    icons = {
        "match_event": "⚽",
        "wayfinding": "🧭",
        "crowd": "🎉",
        "medical": "🏥",
        "security": "🔒",
        "evacuation": "🚨",
        "transport": "🚌",
        "info": "ℹ️"
    }
    return icons.get(category, "ℹ️")

def get_severity_color(severity: str) -> str:
    """Get color for severity level."""
    colors = {
        "critical": "#dc2626",
        "warning": "#f59e0b",
        "info": "#3b82f6",
        "crowd": "#8b5cf6"
    }
    return colors.get(severity, "#3b82f6")

def get_fallback_translations(text: str) -> dict:
    """Provide high-quality static translations for timeline and fallback announcements."""
    text_lower = text.lower()
    
    if "welcome to the stadium" in text_lower:
        return {
            "en": "Welcome to the stadium! Today's highly anticipated match is between Brazil and Belgium.",
            "hi": "स्टेडियम में आपका स्वागत है! आज का बहुप्रतीक्षित मुकाबला ब्राजील और बेल्जियम के बीच है।",
            "es": "¡Bienvenidos al estadio! El partido más esperado de hoy es entre Brasil y Bélgica.",
            "fr": "Bienvenue au stade! Le match très attendu d'aujourd'hui oppose le Brésil et la Belgique.",
            "ar": "مرحباً بكم في الملعب! مباراة اليوم المرتقبة هي بين البرازيل وبلجيكا.",
            "pt": "Bem-vindo ao estádio! O jogo mais esperado de hoje é entre Brasil e Bélgica.",
            "zh": "欢迎来到体育场！今天备受期待的比赛是在巴西和比利时之间进行。"
        }
    elif "belgium scores" in text_lower or "belgium responds" in text_lower:
        return {
            "en": "GOAL! Belgium scores/responds with a brilliant strike!",
            "hi": "गोल! बेल्जियम ने शानदार गोल किया!",
            "es": "¡GOL! Bélgica marca con un disparo brillante.",
            "fr": "BUT! La Belgique marque d'une frappe brillante.",
            "ar": "هدف! بلجيكا تسجل بتسديدة رائعة.",
            "pt": "GOL! Bélgica marca com um chute brilhante.",
            "zh": "进球！比利时踢进精彩一球。"
        }
    elif "medical team" in text_lower:
        return {
            "en": "Medical team to Section 114.",
            "hi": "चिकित्सा दल धारा 114 पर पहुंचे।",
            "es": "Equipo médico a la Sección 114.",
            "fr": "Équipe médicale à la section 114.",
            "ar": "فريق طبي إلى القسم 114.",
            "pt": "Equipe médica para a Seção 114.",
            "zh": "医疗队请到114区。"
        }
    elif "aisles clear" in text_lower:
        return {
            "en": "Please keep aisles clear near Section 114.",
            "hi": "कृपया धारा 114 के पास गलियारों को खाली रखें।",
            "es": "Por favor, mantenga los pasillos despejados cerca de la Sección 114.",
            "fr": "Veuillez garder les allées libres près de la section 114.",
            "ar": "يرجى الحفاظ على الممرات خالية بالقرب من القسم 114.",
            "pt": "Por favor, mantenha os corredores livres perto da Seção 114.",
            "zh": "请保持114区附近的走道畅通。"
        }
    elif "brazil scores" in text_lower or "brazil takes" in text_lower:
        return {
            "en": "GOAL! Brazil scores/takes their chance!",
            "hi": "गोल! ब्राजील ने अपना मौका भुनाया!",
            "es": "¡GOL! Brasil aprovecha su oportunidad.",
            "fr": "BUT! Le Brésil saisit sa chance.",
            "ar": "هدف! البرازيل تستغل فرقتها.",
            "pt": "GOL! Brasil aproveita sua chance.",
            "zh": "进球！巴西抓住机会进球。"
        }
    elif "evacuation" in text_lower:
        return {
            "en": "EVACUATION DRILL: Proceed calmly to nearest exit.",
            "hi": "निकासी अभ्यास: कृपया शांतिपूर्वक निकटतम निकास की ओर बढ़ें।",
            "es": "SIMULACRO DE EVACUACIÓN: Por favor, proceda con calma a la salida más cercana.",
            "fr": "EXERCICE D'ÉVACUATION: Veuillez vous diriger calmement vers la sortie la plus proche.",
            "ar": "تدريب إخلاء: يرجى التوجه بهدوء إلى أقرب مخرج.",
            "pt": "SIMULADO DE EVACUAÇÃO: Por favor, dirija-se com calma à saída mais próxima.",
            "zh": "疏散演习：请冷静地前往最近的出口。"
        }
    elif "yellow card" in text_lower:
        return {
            "en": "Yellow card shown.",
            "hi": "पीला कार्ड दिखाया गया।",
            "es": "Tarjeta amarilla mostrada.",
            "fr": "Carton jaune distribué.",
            "ar": "بطاقة صفراء.",
            "pt": "Cartão amarelo mostrado.",
            "zh": "出示黄牌。"
        }
    return {
        "en": text,
        "hi": text,
        "es": text,
        "fr": text,
        "ar": text,
        "pt": text,
        "zh": text
    }

async def transform_announcement(raw_event: dict) -> dict:
    """Transform a raw stadium event into an accessible, translated announcement via Claude AI."""
    event_type = raw_event.get("type", "pa_announcement")
    original_text = raw_event.get("original", "")

    # Try to use Claude for transformation & translation
    try:
        anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

        if event_type == "match_event":
            prompt = f"""You are an accessibility assistant for a stadium. Transform this match event into accessible, emotional content.

Original: {original_text}

The fan is deaf/hard-of-hearing. Create:
1. plain_language: A short, action-first version (max 20 words)
2. description: An emotional description that captures the atmosphere (for goals/crowd reactions)
3. category: {raw_event.get('category', 'match_event')}
4. severity: {raw_event.get('severity', 'info')}
5. icon: ⚽
6. translated: A dictionary containing the translation of the plain_language text into 'hi' (Hindi), 'es' (Spanish), 'fr' (French), 'ar' (Arabic), 'pt' (Portuguese), and 'zh' (Chinese).

Respond as JSON:
{{"plain_language": "...", "description": "...", "category": "...", "severity": "...", "translated": {{"hi": "...", "es": "...", "fr": "...", "ar": "...", "pt": "...", "zh": "..."}}}}"""
        elif event_type == "evacuation_drill":
            prompt = f"""You are an accessibility assistant. NEVER soften or obscure safety-critical messages.

Original: {original_text}

Transform into:
1. plain_language: Urgent, clear action (max 10 words) - preserve urgency exactly
2. category: evacuation
3. severity: critical
4. needs_avatar: true
5. icon: 🚨
6. translated: A dictionary containing the translation of the plain_language text into 'hi' (Hindi), 'es' (Spanish), 'fr' (French), 'ar' (Arabic), 'pt' (Portuguese), and 'zh' (Chinese).

Respond as JSON:
{{"plain_language": "...", "category": "evacuation", "severity": "critical", "needs_avatar": true, "translated": {{"hi": "...", "es": "...", "fr": "...", "ar": "...", "pt": "...", "zh": "..."}}}}"""
        else:
            prompt = f"""You are an accessibility assistant for a stadium. Transform this announcement into plain language.

Original: {original_text}

Transform into:
1. plain_language: Short, simple, action-first (max 15 words)
2. category: {raw_event.get('category', 'info')}
3. severity: {raw_event.get('severity', 'info')}
4. icon: {get_icon_for_category(raw_event.get('category', 'info'), raw_event.get('severity', 'info'))}
5. translated: A dictionary containing the translation of the plain_language text into 'hi' (Hindi), 'es' (Spanish), 'fr' (French), 'ar' (Arabic), 'pt' (Portuguese), and 'zh' (Chinese).

Respond as JSON:
{{"plain_language": "...", "category": "...", "severity": "...", "translated": {{"hi": "...", "es": "...", "fr": "...", "ar": "...", "pt": "...", "zh": "..."}}}}"""

        response = anthropic.messages.create(
            model=model,
            max_tokens=300,
            system="You are a stadium accessibility assistant. Always output valid JSON. Never invent facts.",
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        result_text = response.content[0].text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        ai_result = json.loads(result_text)

        # Build translated mapping
        translations = get_fallback_translations(original_text)
        if "translated" in ai_result and isinstance(ai_result["translated"], dict):
            translations.update(ai_result["translated"])
        translations["en"] = ai_result.get("plain_language", original_text)

        return {
            **raw_event,
            "plain_language": ai_result.get("plain_language", original_text),
            "description": ai_result.get("description"),
            "category": ai_result.get("category", raw_event.get("category", "info")),
            "severity": ai_result.get("severity", raw_event.get("severity", "info")),
            "needs_avatar": ai_result.get("needs_avatar", False),
            "translated": translations,
            "icon": ai_result.get("icon", get_icon_for_category(ai_result.get("category", raw_event.get("category", "info")), ai_result.get("severity", raw_event.get("severity", "info"))))
        }

    except Exception as e:
        print(f"AI transform failed, using fallback: {e}")
        # Fallback: use simple transformation and static translations
        plain_lang = raw_event.get("original", "")
        fallback_trans = get_fallback_translations(plain_lang)
        fallback_trans["en"] = plain_lang
        return {
            **raw_event,
            "plain_language": plain_lang,
            "category": raw_event.get("category", "info"),
            "severity": raw_event.get("severity", "info"),
            "needs_avatar": raw_event.get("type") == "evacuation_drill",
            "translated": fallback_trans,
            "icon": get_icon_for_category(raw_event.get("category", "info"), raw_event.get("severity", "info"))
        }

# =====================
# Event Simulator
# =====================

async def run_demo_timeline():
    """Run the pre-recorded demo timeline, broadcasting events sequentially."""
    for item in TIMELINE.get("timeline", []):
        await asyncio.sleep(item.get("delay", 0))

        raw_event = item.get("event", {})

        # Process through Pipeline A
        announcement = await transform_announcement(raw_event)

        # Add metadata
        announcement["id"] = f"ann_{int(time.time() * 1000)}"
        announcement["timestamp"] = time.time()

        # Store
        announcements.append(announcement)

        # Broadcast to fans
        await broadcast_to_fans(announcement)

# =====================
# API Endpoints
# =====================

@api_router.get("/")
async def root():
    """Health check endpoint — returns API status."""
    return {"message": "StadiumSense API v1.0", "status": "running"}

@api_router.get("/timeline")
async def get_timeline():
    """Return the full match timeline data used for the demo."""
    return TIMELINE

@api_router.post("/demo/run")
async def run_demo():
    """Start the demo timeline as a background task."""
    asyncio.create_task(run_demo_timeline())
    return {"message": "Demo started", "status": "running"}

@api_router.get("/announcements")
async def get_announcements(limit: int = 20):
    """Return the most recent processed announcements (default: last 20)."""
    return announcements[-limit:]

@api_router.post("/ingest")
async def ingest_event(event: dict):
    """Ingest a raw event, transform it via AI Pipeline A, and broadcast to fans."""
    announcement = await transform_announcement(event)
    announcement["id"] = f"ann_{int(time.time() * 1000)}"
    announcement["timestamp"] = time.time()
    announcements.append(announcement)
    await broadcast_to_fans(announcement)
    return announcement

@api_router.post("/broadcast")
async def broadcast(broadcast: BroadcastRequest):
    """Staff composes and broadcasts an accessibility announcement to all fans."""
    event = {
        "type": "staff_broadcast",
        "original": broadcast.message,
        "category": broadcast.category,
        "severity": broadcast.severity
    }
    announcement = await transform_announcement(event)
    announcement["id"] = f"ann_{int(time.time() * 1000)}"
    announcement["timestamp"] = time.time()
    announcements.append(announcement)
    await broadcast_to_fans(announcement)
    return {"status": "broadcasted", "announcement": announcement}

# =====================
# Pipeline B: RAG Q&A
# =====================

# In-memory cache for Q&A answers
qa_cache = {}

@api_router.post("/ask", dependencies=[Depends(check_ask_rate_limit)])
async def ask_question(request: QuestionRequest):
    """Pipeline B: RAG Q&A — answer stadium questions grounded in the knowledge base."""
    # Check cache
    cache_key = (request.question.strip().lower(), request.language, request.location)
    if cache_key in qa_cache:
        cached_result, cached_time = qa_cache[cache_key]
        if time.time() - cached_time < 300:  # 5 min TTL
            return cached_result

    if not kb_index or not embedding_model:
        return {
            "answer": "I'm having trouble accessing the stadium knowledge base. Please ask a nearby volunteer for help.",
            "citations": [],
            "language": request.language
        }

    try:
        # Embed the question
        query_embedding = embedding_model.encode([request.question])
        query_embedding = np.array(query_embedding).astype('float32')

        # Search
        k = 3
        distances, indices = kb_index.search(query_embedding, k)

        # Get relevant chunks
        retrieved_chunks = [kb_chunks[i] for i in indices[0]]

        # Use Claude for answer
        anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

        context = "\n\n---\n\n".join([f"[Chunk {i+1}]: {chunk}" for i, chunk in enumerate(retrieved_chunks)])

        location_context = f" User is near {request.location}." if request.location else ""

        prompt = f"""You are a stadium accessibility assistant. Answer the user's question based ONLY on the provided knowledge base chunks.

User Question: {request.question}
User Language: {request.language}
{location_context}

Knowledge Base Chunks:
{context}

Instructions:
1. Answer based ONLY on the chunks provided
2. If the info is not in the chunks, say "I don't have that information. Please ask a nearby volunteer."
3. Make the answer location-aware if the user provided a location
4. Respond in the user's chosen language if possible
5. Cite which chunk(s) you used

Respond as JSON:
{{"answer": "...", "citations": ["chunk reference 1", "chunk reference 2"]}}"""

        response = anthropic.messages.create(
            model=model,
            max_tokens=500,
            system="You are a stadium accessibility assistant. Always output valid JSON.",
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        result = json.loads(result_text)
        ans_payload = {
            "answer": result.get("answer", "I don't have that information."),
            "citations": result.get("citations", []),
            "language": request.language
        }

        # Cache result
        qa_cache[cache_key] = (ans_payload, time.time())
        return ans_payload

    except Exception as e:
        print(f"Q&A error: {e}")
        return {
            "answer": "I'm having trouble answering your question. Please ask a nearby volunteer for help.",
            "citations": [],
            "language": request.language
        }


# =====================
# Pipeline C: Step-Free Navigation
# =====================

def find_step_free_path(start: str, end: str, graph: dict) -> list[dict]:
    """Find step-free path using simple BFS."""
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])

    # Build adjacency list with step-free filtering
    adj = {}
    for node in nodes:
        adj[node] = []

    for edge in edges:
        from_node = edge.get("from")
        to_node = edge.get("to")

        # Check if both nodes are step-free
        if nodes.get(from_node, {}).get("step_free", False) and nodes.get(to_node, {}).get("step_free", False):
            adj[from_node].append((to_node, edge.get("distance", 10)))
            adj[to_node].append((from_node, edge.get("distance", 10)))

    # BFS
    queue = [(start, [start])]
    visited = {start}

    while queue:
        current, path = queue.pop(0)

        if current == end:
            return path

        for next_node, distance in adj.get(current, []):
            if next_node not in visited:
                visited.add(next_node)
                queue.append((next_node, path + [next_node]))

    return []

@api_router.post("/route", dependencies=[Depends(check_route_rate_limit)])
async def get_route(request: RouteRequest):
    """Pipeline C: step-free pathfinding with LLM turn-by-turn narration for wheelchair users."""
    graph = GRAPH

    # Find path
    path = find_step_free_path(request.start, request.destination, graph)

    if not path:
        return {
            "route": [],
            "description": "No step-free route found. Please contact a volunteer for assistance.",
            "step_free": False
        }

    # Build route details
    nodes = graph.get("nodes", {})
    route_details = []
    total_distance = 0

    for i, node_id in enumerate(path):
        node = nodes.get(node_id, {})
        if i > 0:
            # Calculate distance
            prev = nodes.get(path[i-1], {})
            dist = ((node.get("x", 0) - prev.get("x", 0))**2 + (node.get("y", 0) - prev.get("y", 0))**2)**0.5
            total_distance += dist

        route_details.append({
            "node": node_id,
            "name": node.get("name", node_id),
            "type": node.get("type", "point"),
            "step_free": node.get("step_free", False)
        })

    # Try to use LLM for narration
    try:
        anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")

        prompt = f"""Create a simple turn-by-turn navigation in plain language for a wheelchair user.

Start: {nodes.get(path[0], {}).get('name', path[0])}
Destination: {nodes.get(path[-1], {}).get('name', path[-1])}

Route steps:
{chr(10).join([f'{i+1}. {nodes.get(n, {}).get("name", n)}' for i, n in enumerate(path)])}

Total distance: ~{int(total_distance)} meters

Create a simple, action-first narration. Respond as JSON:
{{"description": "..."}}"""

        response = anthropic.messages.create(
            model=model,
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]

        result = json.loads(result_text)
        description = result.get("description", "")

    except Exception as e:
        # Fallback narration
        description = f"From {nodes.get(path[0], {}).get('name', path[0])} to {nodes.get(path[-1], {}).get('name', path[-1])}. {len(path)} steps, about {int(total_distance)} meters."

    return {
        "route": path,
        "route_details": route_details,
        "description": description,
        "step_free": True,
        "total_distance": int(total_distance)
    }

# =====================
# Help Requests
# =====================

@api_router.post("/request-help", dependencies=[Depends(check_help_rate_limit)])
async def request_help(request: RequestHelp):
    """Submit an accessibility help request, visible to stadium staff."""
    # Note: `import time` is at the top-level of this module.
    help_req = {
        "id": f"help_{int(time.time() * 1000)}",
        "reason": request.reason,
        "location": request.location,
        "severity": request.severity,
        "timestamp": time.time(),
        "status": "pending"
    }

    help_requests.append(help_req)

    return {"status": "submitted", "request": help_req}

@api_router.get("/help-requests")
async def get_help_requests():
    """Return all submitted accessibility help requests (staff-facing dashboard)."""
    return help_requests

# =====================
# Graph/KB endpoints
# =====================

@api_router.get("/graph")
async def get_graph():
    """Return the stadium step-free navigation graph (nodes + edges)."""
    return GRAPH

@api_router.get("/kb")
async def get_kb():
    """Return the stadium knowledge base markdown and chunked segments."""
    return {"kb": STADIUM_KB, "chunks": kb_chunks}


app.include_router(api_router)

# Mount static files for production (Render)
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        """Serve the frontend SPA; fall back to index.html for client-side routing."""
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
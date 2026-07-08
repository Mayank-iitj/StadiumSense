# StadiumSense

> **Accessibility Copilot for FIFA World Cup 2026 Fans**

*"Everyone hears the match — even when they can't."*

StadiumSense is a real-time accessibility platform built for the **FIFA World Cup 2026** at MetLife Stadium. It converts live stadium announcements and match events into:

- ♿ **Real-time plain-language captions** for deaf/hard-of-hearing fans
- 🌐 **7-language instant translations** (English, Hindi, Spanish, French, Arabic, Portuguese, Chinese)
- 📳 **Haptic vibration alerts** for critical events (evacuation, medical)
- 🗺️ **Step-free navigation** with turn-by-turn directions for wheelchair users
- 🤖 **Grounded AI Q&A** over a stadium knowledge base (RAG + FAISS)

---

## Problem Statement

Over **1 billion people** globally live with some form of disability. Major sporting events are still largely inaccessible — stadium announcements are audio-only, navigation is rarely step-free, and information is rarely available in local languages.

StadiumSense solves this through an **AI-powered accessibility pipeline**:

| Problem | StadiumSense Solution |
|---|---|
| PA announcements are audio-only | Real-time text captions + translations |
| Staff can't reach all fans quickly | WebSocket broadcast to every connected device |
| Wheelchair users don't know step-free routes | BFS pathfinding on a step-free graph + LLM narration |
| Fans can't ask questions in their language | RAG Q&A with Claude AI, responds in user's language |
| Emergency alerts not accessible | Full-screen urgent overlays + haptic alerts |

---

## Quick Start

### Prerequisites

- **Backend**: Python 3.10+, `pip`
- **Frontend**: Node.js 18+, `npm`
- **AI**: Anthropic API key

### 1. Setup

```bash
# Clone and navigate
cd stadium-sense

# Backend
cd backend
cp ../.env.example .env
# Edit .env — add your ANTHROPIC_API_KEY

python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Run

**Terminal 1 — Backend:**
```bash
cd backend
.\venv\Scripts\activate
python main.py
# → http://localhost:8000
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
# → http://localhost:5173
```

### 3. Demo

1. Open http://localhost:5173
2. Select your section and language in Settings
3. Go to Staff view: http://localhost:5173/staff
4. Click **"Run Demo"** — plays a full match timeline (goals, crowd, medical, evacuation)
5. Watch the fan app receive real-time accessible captions

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     Fan Device (PWA)                      │
│  AnnouncementFeed │ StadiumMap │ ChatInterface │ Settings  │
└───────────────────────────┬──────────────────────────────┘
                            │  WebSocket + REST
┌───────────────────────────▼──────────────────────────────┐
│                  FastAPI Backend                          │
│                                                          │
│  Pipeline A: Announcement Transform (Claude AI)          │
│    raw event → plain language + 7 translations           │
│                                                          │
│  Pipeline B: RAG Q&A (FAISS + sentence-transformers)     │
│    question → embed → retrieve → Claude → grounded ans   │
│                                                          │
│  Pipeline C: Step-Free Navigation (BFS + Claude)         │
│    start/end → BFS on step-free graph → LLM narration    │
└──────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Vite + React + TypeScript + Tailwind CSS + PWA |
| Backend | FastAPI + Python 3.10+ |
| AI | Anthropic Claude (Pipelines A, B, C) |
| Embeddings | sentence-transformers + FAISS |
| Real-time | WebSockets |
| Testing | pytest + Vitest + @testing-library/react |

---

## Project Structure

```
stadium-sense/
├── backend/
│   ├── main.py              # FastAPI app — all 3 AI pipelines
│   ├── requirements.txt
│   └── tests/
│       └── test_backend.py  # 35+ backend tests
├── frontend/
│   ├── src/
│   │   ├── components/      # AnnouncementFeed, ChatInterface, StadiumMap, ...
│   │   ├── pages/           # FanApp, StaffView
│   │   └── App.test.tsx     # 35+ frontend component tests
│   └── package.json
├── data/
│   ├── stadium_kb.md        # Knowledge base (facilities, accessibility info)
│   ├── match_timeline.json  # Demo event sequence
│   ├── graph.json           # Step-free navigation graph
│   └── floorplan.svg
├── .env.example
└── README.md
```

---

## Testing

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | (required) |
| `ANTHROPIC_MODEL` | Claude model to use | `claude-sonnet-4-5` |
| `BACKEND_PORT` | Backend server port | `8000` |

---

## Security

- **Rate limiting**: All AI endpoints are rate-limited per IP (10 req/min for Q&A, 15 for routing, 5 for help)
- **Input validation**: All inputs validated via Pydantic with `min_length`/`max_length` constraints
- **CORS**: Restricted to `localhost:5173` and `localhost:8000` in development
- **No sensitive data stored**: No PII collected; help requests are ephemeral in-memory
- See [SECURITY.md](./SECURITY.md) for responsible disclosure.

---

## Accessibility Standards

StadiumSense is designed to meet **WCAG 2.1 AA** standards:
- All interactive elements have descriptive `aria-label` attributes
- High-contrast mode available
- Text size controls (80%–150%)
- Screen-reader compatible announcement feed
- Role attributes (`role="switch"`, `aria-checked`, `aria-expanded`) on all controls

---

## Demo Data Notice

⚠️ All stadium data, match events, and announcements are **synthetic demo data** — not affiliated with FIFA, MetLife Stadium, or any real event.

---

## License

MIT

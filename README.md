# StadiumSense

**Accessibility copilot for FIFA World Cup 2026 fans**

*"Everyone hears the match — even when they can't."*

StadiumSense converts live stadium announcements and match events into real-time accessible captions, translations, and haptic alerts for deaf/hard-of-hearing fans. It also provides step-free navigation and a grounded Q&A system.

---

## Quick Start

### Prerequisites

- **Backend**: Python 3.10+, `pip`
- **Frontend**: Node.js 18+, `npm`
- **AI**: Anthropic API key (for AI pipelines)

### 1. Setup

```bash
# Clone and navigate
cd stadium-sense

# Backend setup
cd backend
cp ../.env.example .env
# Edit .env with your ANTHROPIC_API_KEY

# Create virtual environment and install deps
python -m venv venv
.\venv\Scripts\activate  # Windows
# or: source venv/bin/activate  # macOS/Linux

pip install -r requirements.txt

# Frontend setup (new terminal)
cd ../frontend
npm install
```

### 2. Run

**Terminal 1 - Backend:**
```bash
cd backend
.\venv\Scripts\activate
python main.py
# Runs on http://localhost:8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

### 3. Demo

1. Open http://localhost:5173 in your browser (or on phone)
2. Select your section and language in settings
3. Go to Staff view: http://localhost:5173/staff
4. Click **"Run Demo"** to play the full timeline
5. Watch the fan view at http://localhost:5173/fan

---

## Demo Script (~90 seconds)

| Time | Action |
|------|--------|
| 0:00 | Open fan phone (Priya, Hindi). Shows live feed. |
| 0:10 | Start demo. Wayfinding + concession announcements appear as Hindi captions. |
| 0:25 | **GOAL!** Argentina 2-1 Mexico. Celebratory card + haptic. |
| 0:45 | Priya taps "Ask": "Nearest step-free bathroom?" → grounded answer + map route. |
| 1:05 | Staff broadcasts "Keep aisles clear near Section 114." → appears instantly on fan phone. |
| 1:25 | **EVACUATION DRILL** → full-screen red flash + vibration + urgent message. |
| 1:40 | Closing tagline. |

---

## What the GenAI Is Doing

1. **Pipeline A (Announcement Transform)**:
   - Classifies severity: `info | warning | critical`
   - Translates to fan's language
   - Rewrites to plain language (action-first)
   - Generates emotional match descriptions for goals

2. **Pipeline B (RAG Q&A)**:
   - Embeds question + retrieves from stadium knowledge base
   - Grounds answer in retrieved chunks (citations visible)
   - Location-aware: "From Section 114, nearest step-free restroom is..."

3. **Pipeline C (Route Narration)**:
   - Pathfinds on step-free graph
   - Generates plain-language turn-by-turn directions

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Vite + React + TypeScript + Tailwind + PWA |
| Backend | FastAPI + Python |
| AI | Anthropic Claude (structured JSON) |
| Embeddings | sentence-transformers + FAISS |
| Real-time | WebSockets |

---

## Project Structure

```
stadium-sense/
├── frontend/          # React PWA
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── hooks/
│   └── package.json
├── backend/           # FastAPI
│   ├── main.py
│   └── requirements.txt
├── data/              # Stadium data
│   ├── stadium_kb.md  # Knowledge base
│   ├── match_timeline.json
│   ├── graph.json
│   └── floorplan.svg
├── .env.example
└── README.md
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key |
| `ANTHROPIC_MODEL` | Model to use (default: claude-sonnet-4-20250514) |
| `BACKEND_PORT` | Port for backend (default: 8000) |

---

## Demo Data Notice

⚠️ All stadium data, match events, and announcements are **synthetic demo data** — not affiliated with FIFA, MetLife Stadium, or any real event.

---

## License

MIT# StadiumSense

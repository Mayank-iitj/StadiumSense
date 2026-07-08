import sys

with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add imports
content = content.replace(
    'from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException',
    'from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, APIRouter\nfrom fastapi.staticfiles import StaticFiles\nfrom fastapi.responses import FileResponse'
)

# Add APIRouter
content = content.replace(
    'app = FastAPI(title="StadiumSense API", version="1.0.0")',
    'app = FastAPI(title="StadiumSense API", version="1.0.0")\napi_router = APIRouter(prefix="/api")'
)

# Change routes
routes_to_change = [
    ('@app.get("/")', '@api_router.get("/")'),
    ('@app.get("/timeline")', '@api_router.get("/timeline")'),
    ('@app.post("/demo/run")', '@api_router.post("/demo/run")'),
    ('@app.get("/announcements")', '@api_router.get("/announcements")'),
    ('@app.post("/ingest")', '@api_router.post("/ingest")'),
    ('@app.post("/broadcast")', '@api_router.post("/broadcast")'),
    ('@app.post("/ask")', '@api_router.post("/ask")'),
    ('@app.post("/route")', '@api_router.post("/route")'),
    ('@app.post("/request-help")', '@api_router.post("/request-help")'),
    ('@app.get("/help-requests")', '@api_router.get("/help-requests")'),
    ('@app.get("/graph")', '@api_router.get("/graph")'),
    ('@app.get("/kb")', '@api_router.get("/kb")')
]

for old, new in routes_to_change:
    content = content.replace(old, new)

# Add inclusion and static files at the bottom before if __name__ == "__main__":
static_files_code = """
app.include_router(api_router)

# Mount static files for production (Render)
frontend_dist = BASE_DIR / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
"""

content = content.replace('if __name__ == "__main__":', static_files_code + '\nif __name__ == "__main__":')

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

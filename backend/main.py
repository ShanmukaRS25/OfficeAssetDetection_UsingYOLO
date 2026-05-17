"""
backend/main.py
---------------
FastAPI application — REST endpoints + WebSocket video stream.

Endpoints
─────────
GET  /                      → serve React build (index.html)
GET  /health                → liveness probe
GET  /api/detections        → recent detection log (SQLite)
GET  /api/counts            → per-label aggregate counts
GET  /api/screenshots       → list of saved screenshots
POST /api/screenshot        → capture a screenshot from live frame
GET  /screenshots/{file}    → serve screenshot image files
WS   /ws/stream             → binary MJPEG + JSON detection metadata
"""

import asyncio
import json
import logging
import os
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.config import APP_HOST, APP_PORT, SCREENSHOT_DIR
from backend.database import (
    fetch_object_counts,
    fetch_recent_detections,
    fetch_screenshots,
    init_db,
    insert_detections,
)
from backend.detector import detector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ─── App factory ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Office Asset Detection API",
    description="Real-time YOLO-powered object detection dashboard",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Lifespan ─────────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup() -> None:
    await init_db()
    detector.start()
    logger.info("DB initialised and detector started.")


@app.on_event("shutdown")
async def shutdown() -> None:
    detector.stop()


# ─── Serve screenshot files ───────────────────────────────────────────────────
app.mount(
    "/screenshots",
    StaticFiles(directory=str(SCREENSHOT_DIR)),
    name="screenshots",
)

# ─── Serve React build (if present) ──────────────────────────────────────────
_FRONTEND_BUILD = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if _FRONTEND_BUILD.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=str(_FRONTEND_BUILD / "assets")),
        name="assets",
    )


@app.get("/", include_in_schema=False, response_model=None)
async def serve_spa():
    index = _FRONTEND_BUILD / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return HTMLResponse(
        "<h2>React build not found — run <code>npm run build</code> in /frontend</h2>",
        status_code=200,
    )


# ─── Health ───────────────────────────────────────────────────────────────────
@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "frame_count": detector.frame_count}


# ─── REST API ─────────────────────────────────────────────────────────────────
@app.get("/api/detections")
async def api_detections(limit: int = 200) -> JSONResponse:
    rows = await fetch_recent_detections(limit)
    return JSONResponse(content=rows)


@app.get("/api/counts")
async def api_counts() -> JSONResponse:
    rows = await fetch_object_counts()
    return JSONResponse(content=rows)


@app.get("/api/screenshots")
async def api_screenshots(limit: int = 50) -> JSONResponse:
    rows = await fetch_screenshots(limit)
    return JSONResponse(content=rows)


@app.post("/api/screenshot")
async def api_capture_screenshot() -> JSONResponse:
    result = await detector.capture_screenshot()
    return JSONResponse(content=result)


# ─── WebSocket stream ─────────────────────────────────────────────────────────
@app.websocket("/ws/stream")
async def ws_stream(ws: WebSocket) -> None:
    await ws.accept()
    logger.info("WebSocket client connected: %s", ws.client)

    # Each WebSocket gets its own async queue bridged from the detector thread
    q: asyncio.Queue = asyncio.Queue(maxsize=4)

    async def _pump() -> None:
        """Poll the detector's latest frame and push to the per-client async queue."""
        try:
            last_frame = -1
            while True:
                jpeg = None
                meta = None
                frame_id = -1
                
                with detector._lock:
                    if detector.frame_count > last_frame and detector.latest_jpeg:
                        jpeg = detector.latest_jpeg
                        meta = detector.latest_meta
                        frame_id = detector.frame_count
                        last_frame = frame_id
                
                if jpeg:
                    try:
                        q.put_nowait((jpeg, meta, frame_id))
                    except asyncio.QueueFull:
                        pass  # Skip; client is lagging
                
                # Poll at ~30 FPS
                await asyncio.sleep(1/30)
        except Exception as e:
            logger.error("Error in _pump task: %s", e)

    pump_task = asyncio.create_task(_pump())

    try:
        while True:
            try:
                jpeg, meta, frame_id = await asyncio.wait_for(
                    q.get(), timeout=2.0
                )
            except asyncio.TimeoutError:
                # Send a keep-alive ping
                await ws.send_text(json.dumps({"type": "ping"}))
                continue

            # ── Persist detections every 10th frame to avoid DB flooding ──
            if frame_id % 10 == 0:
                asyncio.create_task(insert_detections(meta))

            # ── Send frame: binary JPEG ────────────────────────────────────
            await ws.send_bytes(jpeg)

            # ── Send metadata: JSON text ───────────────────────────────────
            payload = {
                "type": "detections",
                "frame_id": frame_id,
                "detections": meta,
                "counts": _aggregate_counts(meta),
            }
            await ws.send_text(json.dumps(payload))
            
            # Limit to ~15 FPS to avoid overwhelming the frontend
            await asyncio.sleep(1/15)

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected: %s", ws.client)
    finally:
        pump_task.cancel()


def _aggregate_counts(meta: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for d in meta:
        counts[d["label"]] = counts.get(d["label"], 0) + 1
    return counts


# ─── Dev runner ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=APP_HOST,
        port=APP_PORT,
        reload=False,   # reload=True breaks the camera thread
        log_level="info",
    )

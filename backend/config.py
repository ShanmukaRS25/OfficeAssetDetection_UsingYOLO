"""
backend/config.py
-----------------
Centralised configuration loaded from .env / environment variables.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

# Server
APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

# YOLO
YOLO_MODEL: str = os.getenv("YOLO_MODEL", "yolov8m.pt")
CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.25"))

# Camera
CAMERA_INDEX: int | str = os.getenv("CAMERA_INDEX", "0")
try:
    CAMERA_INDEX = int(CAMERA_INDEX)
except ValueError:
    pass  # RTSP URL — keep as string

# Target classes (comma-separated in .env)
_raw_classes = os.getenv(
    "TARGET_CLASSES",
    "person,laptop,cell phone,bottle,chair,keyboard,mouse,book",
)
TARGET_CLASSES: list[str] = [c.strip() for c in _raw_classes.split(",")]

# Storage paths (relative to repo root)
ROOT_DIR: Path = Path(__file__).resolve().parents[1]
SCREENSHOT_DIR: Path = ROOT_DIR / os.getenv("SCREENSHOT_DIR", "screenshots")
DB_PATH: Path = ROOT_DIR / os.getenv("DB_PATH", "data/detections.db")
LOG_DIR: Path = ROOT_DIR / os.getenv("LOG_DIR", "logs")

# Create directories on import
for _d in (SCREENSHOT_DIR, DB_PATH.parent, LOG_DIR):
    _d.mkdir(parents=True, exist_ok=True)

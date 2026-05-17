"""
backend/detector.py
-------------------
Singleton YOLO detector that owns the webcam capture loop.
Pushes annotated JPEG frames and detection metadata to async queues
consumed by the FastAPI WebSocket endpoint.
"""
from __future__ import annotations

import asyncio
import io
import logging
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO

from backend.config import (
    CAMERA_INDEX,
    CONFIDENCE_THRESHOLD,
    SCREENSHOT_DIR,
    TARGET_CLASSES,
    YOLO_MODEL,
)
from backend.database import insert_detections, insert_screenshot

logger = logging.getLogger(__name__)

# ─── Colour palette per class ────────────────────────────────────────────────
_PALETTE = {
    "person":     (0,   200, 100),
    "laptop":     (255, 120,  0),
    "cell phone": (0,   160, 255),
    "bottle":     (200, 60,  255),
    "chair":      (255, 200,   0),
    "keyboard":   (60,  220, 255),
    "mouse":      (255, 60,  120),
    "book":       (80,  255, 180),
}
_DEFAULT_COLOR = (220, 220, 220)


def _color_for(label: str) -> tuple[int, int, int]:
    return _PALETTE.get(label, _DEFAULT_COLOR)


# ─── Detector Singleton ───────────────────────────────────────────────────────
class ObjectDetector:
    """
    Runs YOLO inference in a background thread.
    Exposes:
        • latest_jpeg  – raw bytes of the most-recent annotated frame
        • latest_meta  – list of detection dicts for the most-recent frame
        • frame_count  – rolling frame counter
    """

    def __init__(self) -> None:
        self.model = YOLO(YOLO_MODEL)
        # Build COCO-label → class-id map from the loaded model
        self._target_ids: list[int] = [
            cid
            for cid, name in self.model.names.items()
            if name in TARGET_CLASSES
        ]
        
        id_map = {cid: self.model.names[cid] for cid in self._target_ids}
        logger.info("Detector initialized. Watching classes: %s", id_map)
        
        self._cap: cv2.VideoCapture | None = None
        self._thread: threading.Thread | None = None
        self._running = False

        self.latest_jpeg: bytes = b""
        self.latest_meta: list[dict] = []
        self.frame_count: int = 0
        self._lock = threading.Lock()

    # ─── Lifecycle ────────────────────────────────────────────────────────────
    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True, name="detector")
        self._thread.start()
        logger.info("Detector thread launched for camera %s", CAMERA_INDEX)

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        if self._cap:
            self._cap.release()
        logger.info("Detector stopped.")

    # ─── Capture loop (background thread) ────────────────────────────────────
    def _loop(self) -> None:
        logger.info("Opening camera %s...", CAMERA_INDEX)
        
        def try_open(index, backend=None):
            if backend is not None:
                cap = cv2.VideoCapture(index, backend)
            else:
                cap = cv2.VideoCapture(index)
            
            if cap.isOpened():
                # Test a read
                ok, _ = cap.read()
                if ok:
                    return cap
                cap.release()
            return None

        self._cap = None
        if isinstance(CAMERA_INDEX, int):
            # Try DSHOW first on Windows
            logger.info("Attempting to open camera with CAP_DSHOW...")
            self._cap = try_open(CAMERA_INDEX, cv2.CAP_DSHOW)
            
            if not self._cap:
                logger.info("CAP_DSHOW failed or produced no frames. Trying default backend...")
                self._cap = try_open(CAMERA_INDEX)
        else:
            self._cap = try_open(CAMERA_INDEX)

        if not self._cap or not self._cap.isOpened():
            logger.error("Failed to open camera %s after all attempts", CAMERA_INDEX)
            self._running = False
            return

        # Set standard 640x480 resolution (native size for YOLOv8 inference, highly compatible)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        actual_w = self._cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        actual_h = self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        logger.info("Camera %s opened successfully. Resolution set to: %dx%d", CAMERA_INDEX, actual_w, actual_h)

        while self._running:
            try:
                ok, frame = self._cap.read()
                if not ok:
                    logger.warning("Frame capture failed; retrying…")
                    time.sleep(0.05)
                    continue

                self.frame_count += 1
                annotated, meta = self._infer(frame)

                # Encode to JPEG
                _, buf = cv2.imencode(
                    ".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80]
                )
                jpeg_bytes = buf.tobytes()

                with self._lock:
                    self.latest_jpeg = jpeg_bytes
                    self.latest_meta = meta
                
                if self.frame_count % 30 == 0:
                    logger.info("Processed %d frames", self.frame_count)

            except Exception as e:
                logger.error("Error in detector loop: %s", e, exc_info=True)
                time.sleep(1.0)

    # ─── YOLO inference + annotation ─────────────────────────────────────────
    def _infer(self, frame: np.ndarray) -> tuple[np.ndarray, list[dict]]:
        results = self.model(
            frame,
            classes=self._target_ids,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False,
        )[0]

        meta: list[dict] = []
        annotated = frame.copy()
        h, w = frame.shape[:2]
        
        avg_brightness = frame.mean()
        if self.frame_count % 30 == 0:
            logger.info("Frame %d: Brightness %.1f, Raw YOLO boxes: %d", 
                        self.frame_count, avg_brightness, len(results.boxes))

        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = self.model.names[cls_id]
            conf = float(box.conf[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            color = _color_for(label)

            # ── Draw bounding box ──────────────────────────────────────────
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # ── Label pill ────────────────────────────────────────────────
            text = f"{label}  {conf * 100:.0f}%"
            (tw, th), baseline = cv2.getTextSize(
                text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2
            )
            pill_y = max(y1 - 6, th + 6)
            cv2.rectangle(
                annotated,
                (x1, pill_y - th - 4),
                (x1 + tw + 8, pill_y + baseline),
                color,
                -1,
            )
            cv2.putText(
                annotated,
                text,
                (x1 + 4, pill_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (10, 10, 10),
                2,
                cv2.LINE_AA,
            )

            meta.append(
                {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "label": label,
                    "confidence": round(conf, 4),
                    "bbox_x1": x1,
                    "bbox_y1": y1,
                    "bbox_x2": x2,
                    "bbox_y2": y2,
                    "frame_id": self.frame_count,
                }
            )

        # ── HUD overlay ────────────────────────────────────────────────────
        _draw_hud(annotated, meta, w, h)

        return annotated, meta

    # ─── Screenshot ──────────────────────────────────────────────────────────
    async def capture_screenshot(self) -> dict:
        with self._lock:
            jpeg = self.latest_jpeg
            meta = list(self.latest_meta)

        if not jpeg:
            return {"error": "No frame available yet"}

        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{ts}.jpg"
        filepath = SCREENSHOT_DIR / filename

        # Save raw JPEG
        filepath.write_bytes(jpeg)

        # Persist to DB
        row_id = await insert_screenshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            filename=filename,
            object_count=len(meta),
        )
        return {
            "id": row_id,
            "filename": filename,
            "object_count": len(meta),
            "detections": meta,
        }


# ─── HUD helper ───────────────────────────────────────────────────────────────
def _draw_hud(frame: np.ndarray, meta: list[dict], w: int, h: int) -> None:
    """Draw a translucent top-left HUD with object counts."""
    counts: dict[str, int] = {}
    for d in meta:
        counts[d["label"]] = counts.get(d["label"], 0) + 1

    lines = [f"{lbl}: {cnt}" for lbl, cnt in sorted(counts.items())]
    if not lines:
        lines = ["No objects detected"]

    pad = 10
    line_h = 22
    box_h = pad * 2 + len(lines) * line_h
    box_w = 220

    overlay = frame.copy()
    cv2.rectangle(overlay, (pad, pad), (pad + box_w, pad + box_h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    for i, line in enumerate(lines):
        cv2.putText(
            frame,
            line,
            (pad + 8, pad + (i + 1) * line_h),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 230, 120),
            1,
            cv2.LINE_AA,
        )


# ─── Global detector instance ────────────────────────────────────────────────
detector = ObjectDetector()

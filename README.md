# 🎯 Live Object Detection Dashboard — YOLO POC

A **real-time** office asset detection system powered by **YOLOv8**, **FastAPI**, and **React**.

---

## 📐 Architecture

```
Webcam
  ↓
YOLO Model  (YOLOv8n via Ultralytics)
  ↓
Object Detection + Bounding Boxes
  ↓
FastAPI Backend  (REST + WebSocket)
  ↓  ←→  SQLite (detection logs + screenshots)
React Dashboard  (Live feed · Counts · Log · Gallery)
```

---

## 🗂️ Project Structure

```
OfficeAssetDetection_UsingYOLO/
│
├── backend/
│   ├── __init__.py
│   ├── config.py        ← .env loader (model, camera, thresholds)
│   ├── database.py      ← async SQLite CRUD (aiosqlite)
│   ├── detector.py      ← YOLO inference loop + annotation + screenshot
│   └── main.py          ← FastAPI app (REST + WebSocket /ws/stream)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx                         ← Root (3-tab layout)
│   │   ├── main.jsx
│   │   ├── index.css                       ← Full design system
│   │   ├── hooks/
│   │   │   └── useDetectionStream.js       ← WebSocket hook
│   │   └── components/
│   │       ├── LiveFeed.jsx                ← Annotated video + detection list
│   │       ├── CountDashboard.jsx          ← Stat chips + Recharts bar chart
│   │       ├── EventLog.jsx                ← Auto-refreshing log table
│   │       └── ScreenshotGallery.jsx       ← Gallery with lightbox
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
│
├── screenshots/         ← Captured JPEG screenshots (auto-created)
├── data/                ← SQLite DB file (auto-created)
├── logs/                ← Reserved for CSV / text logs (auto-created)
│
├── .env                 ← Configuration (model, camera, thresholds)
├── requirements.txt     ← Python dependencies
├── start_backend.bat    ← Launch FastAPI
├── start_frontend.bat   ← Launch Vite dev server
└── README.md
```

---

## ⚡ Quick Start

### 1 — Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| Webcam | Any USB / built-in |

### 2 — Python setup (Backend)

```powershell
# From project root
.\yolovenv\Scripts\activate
pip install -r requirements.txt
```

> On first run, YOLO will auto-download `yolov8n.pt` (~6 MB).

### 3 — Start the backend

```powershell
# Option A — batch file
.\start_backend.bat

# Option B — manual
.\yolovenv\Scripts\activate
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Backend runs at → **http://localhost:8000**

### 4 — Start the frontend

```powershell
# Option A — batch file (new terminal)
.\start_frontend.bat

# Option B — manual
cd frontend
npm install
npm run dev
```

Dashboard opens at → **http://localhost:5173**

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness probe |
| `GET` | `/api/detections?limit=N` | Recent detection events |
| `GET` | `/api/counts` | Per-label aggregate counts |
| `GET` | `/api/screenshots?limit=N` | Screenshot metadata list |
| `POST` | `/api/screenshot` | Capture current frame |
| `WS` | `/ws/stream` | Binary JPEG + JSON metadata |

---

## 🎛️ Configuration (`.env`)

| Key | Default | Description |
|-----|---------|-------------|
| `YOLO_MODEL` | `yolov8n.pt` | Model size: n/s/m/l/x |
| `CONFIDENCE_THRESHOLD` | `0.45` | Min detection confidence |
| `CAMERA_INDEX` | `0` | Webcam index or RTSP URL |
| `TARGET_CLASSES` | *(8 classes)* | Comma-separated COCO labels |

---

## 🖥️ Dashboard Features

| Tab | What you see |
|-----|-------------|
| **Live Dashboard** | Annotated webcam feed · per-frame detections · confidence bars · screenshot button |
| **Event Log** | Sortable table of all logged detections with BBox coordinates |
| **Gallery** | Screenshot grid with lightbox · object count per shot |

---

## 🎯 Detected Object Classes & Output Detections

`person` · `laptop` · `cell phone` · `bottle` · `chair` · `keyboard` · `mouse` · `book`
<img width="568" height="396" alt="Book" src="https://github.com/user-attachments/assets/a4bc2d6a-556c-4b0b-b845-d8c8cb00aaf3" />
<img width="225" height="480" alt="Bottle" src="https://github.com/user-attachments/assets/a6181fa1-b098-4852-8150-b0d11c88be74" />
<img width="640" height="480" alt="cell phone" src="https://github.com/user-attachments/assets/ac5b4a11-db0a-47db-a4e9-3d1993c3b3e0" />
<img width="386" height="480" alt="Chair" src="https://github.com/user-attachments/assets/e09a1d4a-dd32-4272-b5a5-291b05bb91f1" />
<img width="640" height="376" alt="Keyboard" src="https://github.com/user-attachments/assets/75971916-6bfd-4a7f-8425-eb12b73f7cb7" />
<img width="640" height="370" alt="Laptop" src="https://github.com/user-attachments/assets/01c38b93-aa6c-4198-b15a-f9d4e1daac8a" />
<img width="640" height="480" alt="Mouse" src="https://github.com/user-attachments/assets/b4dc82b4-6fb9-40ca-ac27-07716779340b" />
<img width="640" height="480" alt="remote" src="https://github.com/user-attachments/assets/aeadb344-6288-4958-bce7-6f84799ea60d" />

---

## Dashboard & Log 
<img width="1528" height="682" alt="Dashboard" src="https://github.com/user-attachments/assets/c45ab9bd-5d7b-4c50-b1af-2d229001a4a5" />
<img width="1536" height="698" alt="Log" src="https://github.com/user-attachments/assets/7a42523c-c80c-49be-9bed-4e0f88c38097" />






---

## 🛠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| Camera not opening | Change `CAMERA_INDEX=1` in `.env` |
| Low FPS | Switch to `YOLO_MODEL=yolov8n.pt` (fastest) |
| CORS errors | Both servers must be running; check proxy in `vite.config.js` |
| Model download fails | Ensure internet access on first run |

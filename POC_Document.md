# Proof of Concept: Office Asset Detection System

## 1. Executive Summary
This Proof of Concept (POC) demonstrates a real-time computer vision system designed to monitor and log office assets using the **YOLOv8** (You Only Look Once) architecture. The system integrates a high-performance Python backend with a modern React dashboard to provide live visual feedback, automated object counting, and a persistent audit trail of detected events.

## 2. Project Objectives
The primary goal of this POC was to build a robust, low-latency monitoring solution capable of:
*   **Real-time Detection:** Identifying common office objects via a standard webcam.
*   **Visual Feedback:** Rendering bounding boxes, labels, and confidence scores directly on the video stream.
*   **Asset Management:** Maintaining a live count of assets (people, laptops, phones, etc.) in the frame.
*   **Data Persistence:** Logging every detection event into a database for historical analysis.
*   **Actionable Intelligence:** Providing tools for manual intervention, such as screenshot capture and a searchable event log.

## 3. Technology Stack
The application utilizes a state-of-the-art "Next Level" tech stack:
*   **Deep Learning:** Ultralytics YOLOv8 (supporting Nano to Medium models).
*   **Backend:** FastAPI (Python) for asynchronous performance and WebSocket handling.
*   **Frontend:** React 18 with Vite for a premium, responsive user interface.
*   **Computer Vision:** OpenCV (Open Source Computer Vision Library).
*   **Database:** SQLite with `aiosqlite` for non-blocking event logging.
*   **Styling:** Vanilla CSS3 with a focus on high-fidelity modern design (Dark Mode).

## 4. System Architecture
The POC follows a decoupled architecture designed for stability and broadcast capability:
1.  **Detector Engine:** A singleton background thread manages the camera hardware and YOLO inference, ensuring that the heavy computation does not block the web server.
2.  **Broadcast Polling:** The backend uses an asynchronous polling mechanism to stream frames. This allows multiple clients to view the live feed simultaneously without performance degradation.
3.  **WebSocket Pipeline:** MJPEG frames and JSON metadata are pushed via WebSockets to provide a sub-100ms latency experience.

## 5. Key Features Implemented

### A. Live Camera Dashboard
A central hub displaying the real-time annotated stream. The UI uses a glassmorphism aesthetic with high-contrast bounding boxes that stay stable even at 30 FPS.

### B. Intelligent Object Counting
The system dynamically aggregates detections per frame, providing an at-a-glance summary of current assets (e.g., "1 Person, 2 Laptops, 1 Mouse").

### C. Detection Event Log
A persistent history table that records:
*   **Object Class** (e.g., cell phone, book)
*   **Confidence Score** (accuracy percentage)
*   **Timestamp** (millisecond precision)
*   **Contextual Metadata** (bounding box coordinates)

### D. Screenshot Gallery
Users can capture high-resolution snapshots of the current detection state. These are stored locally and accessible through a modern thumbnail gallery within the dashboard.

## 6. Engineering Challenges & Solutions

### WebSocket Stabilization
Initial testing revealed connection instability due to React 18's StrictMode. I implemented a robust connection lifecycle manager that prevents infinite reconnection loops and ensures a clean handshake between the frontend and backend.

### Camera Reliability
To support a wide range of hardware on Windows, I implemented a **Multi-Backend Fallback System**. The app attempts to use `CAP_DSHOW` for high-performance capture, with an automatic fallback to the standard system backend if the primary initialization fails.

### Detection Precision
By upgrading the model from YOLOv8-Nano to **YOLOv8-Medium** and lowering the confidence threshold to **0.25**, we successfully improved the detection rate of small or occluded objects like computer mice and handheld mobile phones.

## 7. Conclusion
This POC successfully meets and exceeds all requirements outlined in the project specification. It provides a scalable foundation for a production-grade office monitoring system, combining high-speed AI inference with a professional, user-friendly management interface.

---

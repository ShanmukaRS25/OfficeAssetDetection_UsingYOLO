/**
 * App.jsx
 * -------
 * Root component.  Manages tab navigation between:
 *   1. Live Dashboard  (feed + counts)
 *   2. Event Log       (detection history table)
 *   3. Gallery         (screenshot grid)
 */
import React, { useState } from "react";
import { useDetectionStream } from "./hooks/useDetectionStream";
import { LiveFeed } from "./components/LiveFeed";
import { CountDashboard } from "./components/CountDashboard";
import { EventLog } from "./components/EventLog";
import { ScreenshotGallery } from "./components/ScreenshotGallery";

const TABS = ["Live Dashboard", "Event Log", "Gallery"];

async function captureScreenshot() {
  try {
    const res = await fetch("/api/screenshot", { method: "POST" });
    const data = await res.json();
    if (data.error) {
      alert("Screenshot failed: " + data.error);
    } else {
      // Brief toast-style notification (simple alert for POC)
      console.info("Screenshot saved:", data.filename);
    }
  } catch (e) {
    alert("Screenshot request failed: " + e.message);
  }
}

export default function App() {
  const [activeTab, setActiveTab] = useState(0);
  const { frameSrc, detections, counts, connected } = useDetectionStream();

  return (
    <div className="app">
      {/* ── Topbar ─────────────────────────────────────────────────── */}
      <header className="topbar">
        <div className="topbar-brand">
          <div className="topbar-logo">🎯</div>
          <span className="topbar-title">
            YOLO <span>Detection</span> Dashboard
          </span>
        </div>

        {/* Tab navigation */}
        <nav className="nav-tabs" role="tablist">
          {TABS.map((t, i) => (
            <button
              key={t}
              id={`tab-${t.toLowerCase().replace(/\s+/g, "-")}`}
              className={`nav-tab ${activeTab === i ? "active" : ""}`}
              onClick={() => setActiveTab(i)}
              role="tab"
              aria-selected={activeTab === i}
            >
              {t}
            </button>
          ))}
        </nav>

        {/* Status */}
        <div className="topbar-status">
          <div className={`status-dot ${connected ? "live" : ""}`} />
          {connected ? "Stream connected" : "Reconnecting…"}
        </div>
      </header>

      {/* ── Content ────────────────────────────────────────────────── */}
      <main className="content" role="main">
        {/* Tab 0: Live Dashboard */}
        {activeTab === 0 && (
          <div className="dashboard-grid">
            <LiveFeed
              frameSrc={frameSrc}
              detections={detections}
              connected={connected}
              onScreenshot={captureScreenshot}
            />
            <CountDashboard counts={counts} />
          </div>
        )}

        {/* Tab 1: Event Log */}
        {activeTab === 1 && (
          <div style={{ height: "100%" }}>
            <EventLog />
          </div>
        )}

        {/* Tab 2: Gallery */}
        {activeTab === 2 && (
          <div style={{ height: "100%" }}>
            <ScreenshotGallery />
          </div>
        )}
      </main>
    </div>
  );
}

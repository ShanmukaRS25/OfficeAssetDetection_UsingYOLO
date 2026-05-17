/**
 * LiveFeed.jsx
 * Renders the annotated webcam stream + per-frame detection sidebar.
 */
import React from "react";
import { Camera, Crosshair, Download } from "lucide-react";

// Class → accent colour mapping (mirrors backend palette)
const CLASS_COLORS = {
  person:       "#00e678",
  laptop:       "#ff7800",
  "cell phone": "#00a0ff",
  bottle:       "#c83cff",
  chair:        "#ffc800",
  keyboard:     "#3cdcff",
  mouse:        "#ff3c78",
  book:         "#50ffb4",
};
const DEFAULT_COLOR = "#aab8c8";

function classColor(label) {
  return CLASS_COLORS[label] ?? DEFAULT_COLOR;
}

function ConfBar({ value }) {
  return (
    <div className="conf-bar-wrap">
      <div className="conf-bar" style={{ width: `${Math.round(value * 100)}%` }} />
    </div>
  );
}

export function LiveFeed({ frameSrc, detections, connected, onScreenshot }) {
  return (
    <div className="card" style={{ gridRow: "1 / 3" }}>
      {/* Header */}
      <div className="card-header">
        <span className="card-title">
          <Camera size={15} className="icon" />
          Live Camera Feed
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span className={`badge ${connected ? "badge-green" : "badge-red"}`}>
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: connected ? "var(--accent)" : "var(--danger)",
                display: "inline-block",
              }}
            />
            {connected ? "LIVE" : "OFFLINE"}
          </span>
          <button
            id="btn-screenshot"
            className="btn btn-primary"
            onClick={onScreenshot}
            title="Capture screenshot"
          >
            <Download size={13} />
            Screenshot
          </button>
        </div>
      </div>

      {/* Video */}
      <div className="card-body" style={{ padding: 0, overflow: "hidden" }}>
        <div className="video-wrapper">
          {frameSrc ? (
            <img
              className="video-frame"
              src={frameSrc}
              alt="Live detection feed"
              id="live-video-frame"
            />
          ) : (
            <div className="video-overlay">
              <div className="video-placeholder">
                <div className="big-icon">📷</div>
                <div>
                  {connected ? "Waiting for first frame…" : "Connecting to camera…"}
                </div>
                <div style={{ marginTop: 12 }}>
                  <div className="spinner" style={{ margin: "0 auto" }} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Detection list below video */}
      <div style={{ padding: "14px 18px", borderTop: "1px solid var(--border)" }}>
        <div
          style={{
            fontSize: 12,
            fontWeight: 600,
            color: "var(--text-secondary)",
            marginBottom: 10,
            display: "flex",
            alignItems: "center",
            gap: 6,
          }}
        >
          <Crosshair size={13} style={{ color: "var(--accent)" }} />
          Detections this frame ({detections.length})
        </div>
        <div className="detection-list">
          {detections.length === 0 ? (
            <div
              style={{
                color: "var(--text-muted)",
                fontSize: 13,
                textAlign: "center",
                padding: "16px 0",
              }}
            >
              No objects detected
            </div>
          ) : (
            detections.map((d, i) => (
              <div className="detection-item" key={i}>
                <div
                  className="det-dot"
                  style={{ background: classColor(d.label) }}
                />
                <span className="det-label">{d.label}</span>
                <ConfBar value={d.confidence} />
                <span className="det-conf">
                  {(d.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

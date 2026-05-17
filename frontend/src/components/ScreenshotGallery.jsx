/**
 * ScreenshotGallery.jsx
 * ---------------------
 * Grid of captured screenshots with metadata, served from /api/screenshots.
 */
import React, { useEffect, useState } from "react";
import { Image as ImageIcon, RefreshCw } from "lucide-react";

function formatTs(iso) {
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

export function ScreenshotGallery() {
  const [shots, setShots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [preview, setPreview] = useState(null);

  const fetchShots = async () => {
    try {
      const res = await fetch("/api/screenshots?limit=50");
      const data = await res.json();
      setShots(data);
    } catch (_) {}
    finally { setLoading(false); }
  };

  useEffect(() => {
    fetchShots();
    const id = setInterval(fetchShots, 8000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="card" style={{ height: "100%" }}>
      <div className="card-header">
        <span className="card-title">
          <ImageIcon size={15} className="icon" />
          Screenshot Gallery
        </span>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span className="badge badge-blue">{shots.length} saved</span>
          <button
            className="btn btn-ghost"
            onClick={fetchShots}
            id="btn-refresh-gallery"
            style={{ padding: "5px 10px" }}
          >
            <RefreshCw size={12} />
          </button>
        </div>
      </div>

      <div className="card-body">
        {loading ? (
          <div className="empty-state">
            <div className="spinner" />
            Loading gallery…
          </div>
        ) : shots.length === 0 ? (
          <div className="empty-state">
            📷 No screenshots yet — click "Screenshot" on the live feed
          </div>
        ) : (
          <div className="gallery-grid" id="screenshot-gallery">
            {shots.map((s) => (
              <div
                className="gallery-card"
                key={s.id}
                onClick={() => setPreview(s)}
                id={`gallery-item-${s.id}`}
              >
                <img
                  src={`/screenshots/${s.filename}`}
                  alt={`Screenshot ${s.id}`}
                  loading="lazy"
                />
                <div className="gallery-card-info">
                  <div className="gallery-count">
                    {s.object_count} object{s.object_count !== 1 ? "s" : ""}
                  </div>
                  <div className="gallery-timestamp">{formatTs(s.timestamp)}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Lightbox */}
      {preview && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.85)",
            backdropFilter: "blur(6px)",
            zIndex: 999,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            gap: 16,
          }}
          onClick={() => setPreview(null)}
          id="screenshot-lightbox"
        >
          <img
            src={`/screenshots/${preview.filename}`}
            alt="Preview"
            style={{
              maxWidth: "90vw",
              maxHeight: "80vh",
              borderRadius: 12,
              border: "1px solid var(--border-accent)",
            }}
          />
          <div style={{ color: "var(--text-secondary)", fontSize: 13 }}>
            {preview.filename} · {preview.object_count} objects · {formatTs(preview.timestamp)}
          </div>
          <div style={{ color: "var(--text-muted)", fontSize: 12 }}>
            Click anywhere to close
          </div>
        </div>
      )}
    </div>
  );
}

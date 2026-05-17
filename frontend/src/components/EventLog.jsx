/**
 * EventLog.jsx
 * ------------
 * Tabular log of all detection events fetched from /api/detections.
 * Auto-refreshes every 5 seconds.
 */
import React, { useEffect, useState } from "react";
import { FileText, RefreshCw } from "lucide-react";

function formatTs(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour12: false }) + "." +
      String(d.getMilliseconds()).padStart(3, "0");
  } catch {
    return iso;
  }
}

function confBadge(conf) {
  const pct = Math.round(conf * 100);
  const color =
    pct >= 85 ? "var(--accent)" :
    pct >= 65 ? "var(--warn)"  : "var(--danger)";
  return <span style={{ color, fontWeight: 700 }}>{pct}%</span>;
}

export function EventLog() {
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchLogs = async () => {
    try {
      const res = await fetch("/api/detections?limit=300");
      const data = await res.json();
      setRows(data);
    } catch (_) {}
    finally { setLoading(false); }
  };

  useEffect(() => {
    fetchLogs();
    const id = setInterval(fetchLogs, 5000);
    return () => clearInterval(id);
  }, []);

  return (
    <div className="card" style={{ height: "100%", minHeight: 400 }}>
      <div className="card-header">
        <span className="card-title">
          <FileText size={15} className="icon" />
          Detection Event Log
        </span>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span className="badge badge-blue">{rows.length} events</span>
          <button
            className="btn btn-ghost"
            onClick={fetchLogs}
            id="btn-refresh-log"
            style={{ padding: "5px 10px" }}
          >
            <RefreshCw size={12} />
          </button>
        </div>
      </div>
      <div className="card-body" style={{ padding: 0, overflowX: "auto" }}>
        {loading ? (
          <div className="empty-state">
            <div className="spinner" />
            Loading events…
          </div>
        ) : rows.length === 0 ? (
          <div className="empty-state">No events logged yet</div>
        ) : (
          <table className="log-table" id="detection-log-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Time</th>
                <th>Object</th>
                <th>Confidence</th>
                <th>Frame</th>
                <th>BBox (x1,y1,x2,y2)</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td style={{ color: "var(--text-muted)" }}>{r.id}</td>
                  <td>{formatTs(r.timestamp)}</td>
                  <td style={{ textTransform: "capitalize", fontWeight: 600 }}>
                    {r.label}
                  </td>
                  <td>{confBadge(r.confidence)}</td>
                  <td style={{ color: "var(--text-secondary)" }}>{r.frame_id}</td>
                  <td style={{ color: "var(--text-muted)", fontSize: 11 }}>
                    {r.bbox_x1},{r.bbox_y1},{r.bbox_x2},{r.bbox_y2}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

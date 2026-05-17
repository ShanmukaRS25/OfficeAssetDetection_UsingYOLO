/**
 * CountDashboard.jsx
 * ------------------
 * Shows aggregate per-label counts as stat chips + a recharts bar chart.
 */
import React from "react";
import { BarChart2 } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const COLORS = [
  "#00e678","#00b8ff","#ff7800","#c83cff",
  "#ffc800","#3cdcff","#ff3c78","#50ffb4",
];

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  return (
    <div
      style={{
        background: "var(--bg-card)",
        border: "1px solid var(--border)",
        borderRadius: 8,
        padding: "8px 12px",
        fontSize: 13,
      }}
    >
      <strong style={{ color: "var(--text-primary)" }}>{payload[0].payload.label}</strong>
      <div style={{ color: "var(--accent)", fontFamily: "var(--font-mono)", fontWeight: 700 }}>
        {payload[0].value} detections
      </div>
    </div>
  );
};

export function CountDashboard({ counts }) {
  const data = Object.entries(counts).map(([label, count]) => ({ label, count }));
  const total = data.reduce((s, d) => s + d.count, 0);

  return (
    <>
      {/* Stat chips */}
      <div className="card" style={{ marginBottom: 0 }}>
        <div className="card-header">
          <span className="card-title">
            <BarChart2 size={15} className="icon" />
            Live Object Counts
          </span>
          <span className="badge badge-blue">
            Total: {total}
          </span>
        </div>
        <div className="card-body">
          {data.length === 0 ? (
            <div className="empty-state">No objects in frame</div>
          ) : (
            <>
              <div className="stats-row" id="stats-row-counts">
                {data.map((d, i) => (
                  <div className="stat-chip" key={d.label}>
                    <span
                      className="stat-label"
                      style={{ color: COLORS[i % COLORS.length] }}
                    >
                      {d.label}
                    </span>
                    <span className="stat-value">{d.count}</span>
                  </div>
                ))}
              </div>

              {/* Bar chart */}
              <div className="chart-wrap" style={{ marginTop: 20 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={data}
                    margin={{ top: 4, right: 4, left: -20, bottom: 4 }}
                  >
                    <XAxis
                      dataKey="label"
                      tick={{ fill: "var(--text-secondary)", fontSize: 11 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fill: "var(--text-muted)", fontSize: 10 }}
                      axisLine={false}
                      tickLine={false}
                      allowDecimals={false}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
                    <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                      {data.map((_, i) => (
                        <Cell key={i} fill={COLORS[i % COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}

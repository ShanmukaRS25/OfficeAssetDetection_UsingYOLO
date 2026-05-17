/**
 * useDetectionStream.js
 * ---------------------
 * Custom hook that maintains a WebSocket connection to /ws/stream.
 * Exposes:
 *   frameSrc   – object URL of the latest JPEG frame (string | null)
 *   detections – array of detection objects for the latest frame
 *   counts     – { label: count } map
 *   connected  – boolean
 */
import { useEffect, useRef, useState, useCallback } from "react";

const WS_URL = `${window.location.protocol === "https:" ? "wss" : "ws"}://${
  window.location.hostname
}:8000/ws/stream`;

export function useDetectionStream() {
  const wsRef = useRef(null);
  const [frameSrc, setFrameSrc] = useState(null);
  const [detections, setDetections] = useState([]);
  const [counts, setCounts] = useState({});
  const [connected, setConnected] = useState(false);

  const prevUrlRef = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current) wsRef.current.close();

    const ws = new WebSocket(WS_URL);
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);

    ws.onmessage = (evt) => {
      if (evt.data instanceof ArrayBuffer) {
        // Binary → JPEG frame
        const blob = new Blob([evt.data], { type: "image/jpeg" });
        const url = URL.createObjectURL(blob);
        setFrameSrc((prev) => {
          if (prev) {
            // Delay revoking the old URL to prevent flickering while the new frame renders
            setTimeout(() => URL.revokeObjectURL(prev), 100);
          }
          prevUrlRef.current = url;
          return url;
        });
      } else {
        try {
          const msg = JSON.parse(evt.data);
          if (msg.type === "detections") {
            setDetections(msg.detections || []);
            setCounts(msg.counts || {});
          }
        } catch (_) {}
      }
    };

    ws.onclose = () => {
      // Only auto-reconnect if this is still the active WebSocket
      if (wsRef.current === ws) {
        setConnected(false);
        setTimeout(connect, 2000);
      }
    };

    ws.onerror = () => ws.close();
  }, []);

  useEffect(() => {
    connect();
    return () => {
      if (wsRef.current) {
        const ws = wsRef.current;
        wsRef.current = null; // Clear the ref BEFORE closing so onclose ignores it
        ws.close();
      }
      if (prevUrlRef.current) URL.revokeObjectURL(prevUrlRef.current);
    };
  }, [connect]);

  return { frameSrc, detections, counts, connected };
}

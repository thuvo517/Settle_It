import { useEffect, useRef, useState } from "react";

export function useRoomSocket(code, token, initial) {
  const [state, setState] = useState(initial);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    if (!code || !token) return;
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const base = import.meta.env.VITE_WS_BASE || `${proto}://${window.location.host}`;
    const url = `${base}/ws/rooms/${code}?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);
    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg.type === "state" && msg.state) {
          setState(msg.state);
        }
      } catch {
        /* ignore */
      }
    };

    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 20000);

    return () => {
      clearInterval(ping);
      ws.close();
    };
  }, [code, token]);

  return { state, setState, connected };
}

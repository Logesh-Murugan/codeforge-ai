"use client";

import { useEffect, useRef, useState, useCallback } from "react";

export interface WSFrameData {
  type: "heartbeat" | "status_update" | "agent_event" | "metrics_update" | "timeline_update" | "log_stream";
  project_id: number;
  data: Record<string, any>;
  timestamp: string;
}

export function useMonitoringWebSocket(projectId: number = 1) {
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [lastFrame, setLastFrame] = useState<WSFrameData | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    try {
      const wsUrl = `ws://localhost:8000/ws/monitoring?project_id=${projectId}`;
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        console.log("[WS] Connected to /ws/monitoring");
      };

      ws.onmessage = (event) => {
        try {
          const parsed: WSFrameData = JSON.parse(event.data);
          setLastFrame(parsed);
        } catch (e) {
          console.error("[WS] Frame parse error:", e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log("[WS] Disconnected. Reconnecting in 3s...");
        reconnectTimeoutRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = (error) => {
        console.error("[WS] Error:", error);
        ws.close();
      };

      wsRef.current = ws;
    } catch (err) {
      console.error("[WS] Connection init failed:", err);
      reconnectTimeoutRef.current = setTimeout(connect, 3000);
    }
  }, [projectId]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  return { isConnected, lastFrame };
}

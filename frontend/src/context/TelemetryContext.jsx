import React, { createContext, useContext, useState, useEffect, useRef } from 'react';

const TelemetryContext = createContext();

export const TelemetryProvider = ({ children }) => {
  const [telemetry, setTelemetry] = useState({
    cpu: 0,
    ram: 0,
    totalAgents: 0,
    activeAgents: 0,
    responseMs: 0,
    logs: [],
    signals: [],
    socialEvents: [],
    portfolio: { balance: 0, exposure: 0, pnl: 0 },
    config_ok: true,
    status: 'OFFLINE'
  });
  
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // Support for both dev (localhost) and production (centre.twisterlab.local)
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/ws/telemetry`;
    
    const connect = () => {
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }

      console.log(`[Telemetry] Initiating unique connection to ${wsUrl}`);
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        console.log('[Telemetry] WebSocket established.');
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setTelemetry(prev => {
            let newLogs = prev.logs;
            if (message.logs && Array.isArray(message.logs)) {
              newLogs = message.logs;
            } else if (message.log) {
              newLogs = [message.log, ...prev.logs].slice(0, 50);
            }
            
            return {
              ...prev,
              cpu: message.cpu !== undefined ? message.cpu : prev.cpu,
              ram: message.ram !== undefined ? message.ram : prev.ram,
              totalAgents: message.agents !== undefined ? message.agents : prev.totalAgents,
              activeAgents: message.active_agents !== undefined ? message.active_agents : prev.activeAgents,
              responseMs: message.latency !== undefined ? message.latency : prev.responseMs,
              logs: newLogs,
              config_ok: message.config_ok !== undefined ? message.config_ok : prev.config_ok,
              status: message.status || prev.status,
              timestamp: message.timestamp || prev.timestamp
            };
          });
        } catch (err) {
          console.error("[Telemetry] Message parse error", err);
        }
      };

      ws.onclose = (event) => {
        if (wsRef.current === ws) {
          setIsConnected(false);
          console.log(`[Telemetry] WebSocket closed (code: ${event.code}). Reconnecting...`);
          reconnectTimeoutRef.current = setTimeout(connect, 5000);
        }
      };
      
      ws.onerror = (err) => {
        console.error("[Telemetry] WebSocket error", err);
        ws.close();
      };
    };

    connect();

    return () => {
      console.log('[Telemetry] Cleanup: Tearing down unique connection.');
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  return (
    <TelemetryContext.Provider value={{ telemetry, isConnected }}>
      {children}
    </TelemetryContext.Provider>
  );
};

export const useTelemetry = () => {
  const context = useContext(TelemetryContext);
  if (!context) {
    throw new Error('useTelemetry must be used within a TelemetryProvider');
  }
  return context;
};

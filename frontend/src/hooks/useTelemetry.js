import { useState, useEffect } from 'react';

export const useTelemetry = () => {
  const [telemetry, setTelemetry] = useState({
    cpu: 0,
    ram: 0,
    totalAgents: 0,
    activeAgents: 0,
    responseMs: 0,
    logs: [],
    signals: [],
    socialEvents: [],
    portfolio: { balance: 0, exposure: 0, pnl: 0 }
  });
  
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Protocol relative WebSocket URL so it works through Vite proxy or production
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;
    
    let ws;
    let reconnectTimeout;

    const connect = () => {
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setIsConnected(true);
        console.log('Telemetry WebSocket connected.');
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          setTelemetry(prev => {
            // Use logs array from message if present, otherwise fallback to appending single log
            let newLogs = prev.logs;
            if (message.logs && Array.isArray(message.logs)) {
              newLogs = message.logs;
            } else if (message.log) {
              newLogs = [message.log, ...prev.logs].slice(0, 50);
            }
            
            const newSignals = message.signal ? [message.signal, ...prev.signals].slice(0, 50) : prev.signals;
            
            let newSocialEvents = prev.socialEvents;
            if (message.type === 'social_event' && message.data) {
              newSocialEvents = [message.data, ...prev.socialEvents].slice(0, 50);
            }
            
            return {
              ...prev,
              cpu: message.cpu !== undefined ? message.cpu : prev.cpu,
              ram: message.ram !== undefined ? message.ram : prev.ram,
              totalAgents: message.agents !== undefined ? message.agents : prev.totalAgents,
              activeAgents: message.active_agents !== undefined ? message.active_agents : prev.activeAgents,
              responseMs: message.latency !== undefined ? message.latency : prev.responseMs,
              logs: newLogs,
              signals: newSignals,
              socialEvents: newSocialEvents,
              portfolio: message.portfolio ? { ...prev.portfolio, ...message.portfolio } : prev.portfolio
            };
          });
        } catch (err) {
          console.error("Error parsing telemetry data", err);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        console.log('Telemetry WebSocket disconnected. Reconnecting in 5s...');
        reconnectTimeout = setTimeout(connect, 5000);
      };
      
      ws.onerror = (err) => {
        console.error("WebSocket Error: ", err);
        ws.close();
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimeout);
      if (ws) ws.close();
    };
  }, []);

  return { telemetry, isConnected };
};

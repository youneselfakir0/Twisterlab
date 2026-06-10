import React, { useEffect, useRef } from 'react';

const MatrixTerminal = ({ logs = [] }) => {
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="glass-panel flex-1 flex flex-col overflow-hidden">
      <div className="px-4 py-2 border-b border-white/5 bg-white/5 flex justify-between items-center">
        <span className="text-[10px] font-black tracking-[0.2em] text-cyan/70 uppercase">MCP Activity Live Feed</span>
        <div className="flex gap-1">
          <div className="w-1.5 h-1.5 rounded-full bg-red-500/50" />
          <div className="w-1.5 h-1.5 rounded-full bg-yellow-500/50" />
          <div className="w-1.5 h-1.5 rounded-full bg-green-500/50" />
        </div>
      </div>
      <div 
        ref={scrollRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-[11px] space-y-2 scrollbar-hide"
      >
        {logs.length === 0 ? (
          <div className="text-gray-600 animate-pulse italic">Waiting for MCP transport handshake...</div>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="flex gap-3 group">
              <span className="text-gray-700 shrink-0">[{log.timestamp}]</span>
              <span className={`
                ${log.type === 'tool' ? 'text-cyan' : ''}
                ${log.type === 'result' ? 'text-purple' : ''}
                ${log.type === 'error' ? 'text-red-400' : ''}
                ${log.type === 'info' ? 'text-gray-400' : ''}
              `}>
                <span className="font-bold mr-2 uppercase text-[9px] opacity-70">{log.type}:</span>
                {log.text}
              </span>
            </div>
          ))
        )}
      </div>
      <div className="p-2 bg-black/40 border-t border-white/5 text-[9px] font-mono text-gray-600 flex justify-between">
        <span>STRM: 192.168.0.30:30080/mcp</span>
        <span className="animate-pulse">● CONNECTED</span>
      </div>
    </div>
  );
};

export default MatrixTerminal;

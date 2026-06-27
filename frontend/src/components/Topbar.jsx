import React, { useState, useEffect } from 'react';
import { Shield, Radio, Bell } from 'lucide-react';
import { useTelemetry } from '../hooks/useTelemetry';

const Topbar = () => {
  const [time, setTime] = useState(new Date().toLocaleTimeString());
  const { telemetry } = useTelemetry();

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  const isDegraded = !telemetry.config_ok || telemetry.status === 'DEGRADED';

  return (
    <header className="h-16 flex items-center px-8 gap-6 glass-panel border-b border-white/5 z-50 shrink-0 shadow-[0_4px_20px_rgba(0,0,0,0.4)]">
      <div className={`flex items-center gap-4 px-4 py-1.5 border rounded-lg text-[10px] font-black tracking-widest shrink-0 transition-all duration-500
        ${telemetry.config_ok ? 'bg-[#00f2ff]/5 border-[#00f2ff]/20 text-cyan shadow-[inset_0_0_10px_rgba(0,242,255,0.05)]' : 'bg-amber-500/5 border-amber-500/20 text-amber-500'}`}>
        <Radio size={14} className={telemetry.config_ok ? 'animate-pulse' : ''} />
        FLEET SYNC: <span className="text-white ml-1">{telemetry.config_ok ? 'ENCRYPTED' : 'UNSTABLE'}</span>
      </div>

      <div className={`flex items-center gap-4 px-4 py-1.5 border rounded-lg text-[10px] font-black tracking-widest shrink-0 transition-all duration-500
        ${!isDegraded ? 'bg-[#8b5cf6]/5 border-[#8b5cf6]/20 text-purple shadow-[inset_0_0_10px_rgba(139,92,246,0.05)]' : 'bg-red-500/5 border-red-500/20 text-red-500 shadow-[0_0_15px_rgba(239,68,68,0.1)]'}`}>
        <Shield size={14} className={isDegraded ? 'animate-bounce' : ''} />
        THREAT LEVEL: <span className="text-white ml-1">{isDegraded ? 'CRITICAL' : 'NOMINAL'}</span>
      </div>

      <div className="flex-1" />

      <div className="flex items-center gap-8">
        <div className="flex items-center gap-2 text-gray-500 hover:text-white transition-colors cursor-pointer relative group">
          <Bell size={18} className={isDegraded ? 'text-red-500 animate-pulse' : ''} />
          <div className={`absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full border-2 border-[#020409] ${isDegraded ? 'bg-red-500' : 'bg-transparent'}`} />
        </div>
        
        <div className="h-8 w-px bg-white/10" />

        <div className="flex flex-col items-end shrink-0 min-w-[120px]">
          <div className="text-white font-mono text-[13px] font-bold leading-none tracking-wider">
            {time}
          </div>
          <div className="text-[9px] text-gray-600 font-bold tracking-widest uppercase mt-1.5">
            LOCAL SYSTEM TIME
          </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;

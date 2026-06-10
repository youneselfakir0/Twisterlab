import React, { useState, useEffect } from 'react';
import { Shield, Radio, Bell } from 'lucide-react';

const Topbar = () => {
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="h-16 flex items-center px-8 gap-6 glass-panel border-b border-white/5 z-50 shrink-0">
      <div className="flex items-center gap-4 px-4 py-1.5 bg-black/40 border border-white/5 rounded-lg text-[10px] font-black tracking-widest text-cyan shrink-0">
        <Radio size={14} className="animate-pulse" />
        FLEET SYNC: <span className="text-white ml-1">ENCRYPTED</span>
      </div>

      <div className="flex items-center gap-4 px-4 py-1.5 bg-black/40 border border-white/5 rounded-lg text-[10px] font-black tracking-widest text-purple shrink-0">
        <Shield size={14} />
        THREAT LEVEL: <span className="text-white ml-1">NOMINAL</span>
      </div>

      <div className="flex-1" />

      <div className="flex items-center gap-6">
        <div className="flex items-center gap-2 text-gray-500 hover:text-white transition-colors cursor-pointer relative">
          <Bell size={18} />
          <div className="absolute -top-0.5 -right-0.5 w-2 h-2 bg-red-500 rounded-full border-2 border-bg" />
        </div>
        
        <div className="h-8 w-px bg-white/5" />

        <div className="flex flex-col items-end shrink-0">
          <div className="text-white font-mono text-[13px] font-bold leading-none tracking-wider">
            {time}
          </div>
          <div className="text-[9px] text-gray-500 font-bold tracking-widest uppercase mt-1">
            LOCAL SYSTEM TIME
          </div>
        </div>
      </div>
    </header>
  );
};

export default Topbar;

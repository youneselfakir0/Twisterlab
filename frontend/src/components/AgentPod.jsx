import React from 'react';
import { Activity, Brain, Shield, Zap, Search, Globe, HardDrive, RefreshCw, Cpu, Binary } from 'lucide-react';

const agentIcons = {
  'Maestro': Brain,
  'SentimentAnalyzer': Activity,
  'RealClassifier': Search,
  'DesktopCommander': Cpu,
  'RealBrowser': Globe,
  'RealMonitoring': Activity,
  'RealResolver': Zap,
  'RealBackup': HardDrive,
  'RealSync': RefreshCw,
  'real-odysseus': Binary,
  'odysseus': Binary
};

const AgentPod = ({ name, status = 'idle', latency = '0ms' }) => {
  const Icon = agentIcons[name] || agentIcons[name.toLowerCase()] || Cpu;
  const isActive = status === 'active' || status === 'online';
  const isError = status === 'error';

  return (
    <div className={`glass-panel p-4 relative overflow-hidden group transition-all duration-700 hover:scale-[1.02] 
      ${isActive ? 'neon-border-cyan bg-cyan/5' : 'neon-border-purple hover:neon-border-cyan'}`}>
      
      {/* Glow Effect */}
      {isActive && <div className="absolute -inset-2 bg-cyan/5 blur-2xl pointer-events-none" />}
      
      <div className="flex justify-between items-start mb-4 relative z-10">
        <div className={`p-2.5 rounded-xl bg-black/60 border transition-all duration-500
          ${isActive ? 'border-cyan/50 text-cyan shadow-[0_0_15px_rgba(0,242,255,0.4)]' : 'border-white/10 text-gray-500'}`}>
          <Icon size={20} className={isActive ? 'animate-pulse' : ''} />
        </div>
        <div className="flex flex-col items-end">
          <span className={`text-[10px] font-black tracking-widest ${isActive ? 'text-cyan drop-shadow-[0_0_5px_rgba(0,242,255,0.5)]' : 'text-gray-600'}`}>
            {isActive ? 'ONLINE' : 'IDLE'}
          </span>
          <span className="text-[9px] text-gray-700 font-mono font-bold mt-1 tracking-tighter">{latency}</span>
        </div>
      </div>
      
      <div className="space-y-1 relative z-10">
        <div className="text-[13px] font-black tracking-[0.15em] text-white uppercase group-hover:text-cyan transition-colors">{name}</div>
        <div className="text-[10px] text-gray-500 font-medium leading-relaxed truncate">
          {isActive ? 'Autonomous: Interfacing neural core...' : 'Standby: Heartbeat normal.'}
        </div>
      </div>

      {isActive && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-cyan shadow-[0_0_10px_#00f2ff] overflow-hidden">
          <div className="h-full bg-white/40 w-1/3 animate-[scan_3s_linear_infinite]" />
        </div>
      )}
      
      <div className="absolute top-0 right-0 p-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
        <div className={`w-1.5 h-1.5 rounded-full animate-ping ${isActive ? 'bg-cyan' : 'bg-purple'}`} />
      </div>
    </div>
  );
};

export default AgentPod;

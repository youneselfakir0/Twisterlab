import React from 'react';
import { Activity, Brain, Shield, Zap, Search, Globe, HardDrive, RefreshCw, Cpu } from 'lucide-react';

const agentIcons = {
  'Maestro': Brain,
  'SentimentAnalyzer': Activity,
  'RealClassifier': Search,
  'DesktopCommander': Cpu,
  'RealBrowser': Globe,
  'RealMonitoring': Activity,
  'RealResolver': Zap,
  'RealBackup': HardDrive,
  'RealSync': RefreshCw
};

const AgentPod = ({ name, status = 'idle', latency = '0ms' }) => {
  const Icon = agentIcons[name] || Cpu;
  const isActive = status === 'active';
  const isError = status === 'error';

  return (
    <div className={`glass-panel p-4 relative overflow-hidden group transition-all duration-500 hover:neon-border-cyan ${isActive ? 'neon-border-cyan' : ''}`}>
      <div className="flex justify-between items-start mb-4">
        <div className={`p-2 rounded bg-black/40 border ${isActive ? 'border-cyan/50 text-cyan shadow-[0_0_10px_rgba(0,242,255,0.3)]' : 'border-white/5 text-gray-500'}`}>
          <Icon size={20} />
        </div>
        <div className="flex flex-col items-end">
          <span className={`text-[10px] font-mono font-bold ${isActive ? 'text-cyan' : 'text-gray-500'}`}>
            {isActive ? '● EXECUTING' : '○ IDLE'}
          </span>
          <span className="text-[9px] text-gray-600 font-mono">{latency}</span>
        </div>
      </div>
      
      <div className="space-y-1">
        <div className="text-[12px] font-black tracking-wider text-white uppercase">{name}</div>
        <div className="text-[10px] text-gray-500 font-mono truncate">
          {isActive ? 'Autonomous: Monitoring neural pipeline...' : 'Standby: Monitoring heartbeat...'}
        </div>
      </div>

      {isActive && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-cyan shadow-[0_0_8px_#00f2ff] overflow-hidden">
          <div className="h-full bg-white/50 w-1/3 animate-[scan_2s_linear_infinite]" />
        </div>
      )}
      
      <div className="absolute top-0 right-0 p-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <div className="w-1 h-1 bg-cyan rounded-full animate-ping" />
      </div>
    </div>
  );
};

export default AgentPod;

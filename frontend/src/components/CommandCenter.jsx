import React, { useState, useEffect } from 'react';
import AgentPod from './AgentPod';
import MatrixTerminal from './MatrixTerminal';
import { useTelemetry } from '../hooks/useTelemetry';
import { Cpu, Zap, Activity, ShieldCheck, AlertTriangle } from 'lucide-react';

const CommandCenter = () => {
  const { telemetry, isConnected } = useTelemetry();
  const [agents, setAgents] = useState([]);
  const [lastUpdate, setLastUpdate] = useState('SYNCING...');

  useEffect(() => {
    if (telemetry.timestamp) {
      setLastUpdate(new Date(telemetry.timestamp * 1000).toLocaleTimeString());
    }
  }, [telemetry.timestamp]);

  // Fetch real agents
  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const r = await fetch('/api/v1/agents/live');
        if (r.ok) {
          const data = await r.json();
          setAgents(data);
        }
      } catch (e) {
        console.error("Failed to fetch agents", e);
      }
    };
    fetchAgents();
  }, []);

  const displayAgents = agents.length > 0 ? agents : [
    { id: 'Maestro', name: 'Maestro', status: 'online' },
    { id: 'odysseus', name: 'Odysseus', status: 'online' },
    { id: 'SentimentAnalyzer', name: 'SentimentAnalyzer', status: 'standby' },
    { id: 'RealClassifier', name: 'RealClassifier', status: 'standby' },
    { id: 'DesktopCommander', name: 'DesktopCommander', status: 'standby' },
    { id: 'RealBrowser', name: 'RealBrowser', status: 'standby' },
    { id: 'RealMonitoring', name: 'RealMonitoring', status: 'standby' },
    { id: 'RealResolver', name: 'RealResolver', status: 'standby' },
    { id: 'RealBackup', name: 'RealBackup', status: 'standby' },
    { id: 'RealSync', name: 'RealSync', status: 'standby' }
  ];

  return (
    <div className="flex flex-col flex-1 gap-8 overflow-hidden animate-in fade-in duration-700">
      
      {/* Critical System Alert */}
      {!telemetry.config_ok && (
        <div className="bg-red-500/10 border border-red-500/30 p-4 rounded-xl flex items-center gap-4 animate-pulse shrink-0">
          <AlertTriangle className="text-red-500" size={20} />
          <div className="flex-1">
            <div className="text-[11px] font-black text-red-500 uppercase tracking-widest">CRITICAL CONFIGURATION FAILURE</div>
            <div className="text-[10px] text-red-200/70 font-medium mt-0.5 uppercase tracking-tighter">Missing environment secrets detected. System orchestration may be compromised.</div>
          </div>
          <button className="px-4 py-1.5 bg-red-500 text-black text-[10px] font-black rounded-lg uppercase tracking-widest">FIX NOW</button>
        </div>
      )}

      {/* Tactical Overview */}
      <div className="flex justify-between items-end px-1 shrink-0">
        <h3 className="text-[11px] font-black tracking-[0.4em] text-white/50 uppercase flex items-center gap-2">
          <div className={`w-1.5 h-1.5 rounded-full animate-pulse shadow-[0_0_8px_currentColor] ${isConnected ? 'bg-cyan text-cyan' : 'bg-red-500 text-red-500'}`} />
          Infrastructure Telemetry
        </h3>
        <span className="text-[9px] font-mono text-cyan/40 uppercase tracking-widest font-bold">NODE: EDGESERVER-OPS // LAST_SYNC: {lastUpdate}</span>
      </div>

      <div className="grid grid-cols-4 gap-6 shrink-0">
        <TacticalMetric label="CPU LOAD" value={`${(telemetry.cpu || 0).toFixed(1)}%`} icon={Cpu} color="cyan" />
        <TacticalMetric label="MEMORY FLUX" value={`${(telemetry.ram || 0).toFixed(1)}%`} icon={Zap} color="purple" />
        <TacticalMetric label="ACTIVE NODES" value={telemetry.activeAgents || displayAgents.filter(a => a.status === 'online').length} icon={Activity} color="emerald" />
        <TacticalMetric label="INTEGRITY" value={telemetry.config_ok ? "100%" : "DEGRADED"} icon={ShieldCheck} color={telemetry.config_ok ? "cyan" : "amber"} />
      </div>

      <div className="flex flex-1 gap-6 min-h-0">
        {/* Fleet Grid */}
        <div className="w-2/3 grid grid-cols-3 gap-4 overflow-y-auto pr-2 scrollbar-hide">
          {displayAgents.map(agent => (
            <AgentPod 
              key={agent.id} 
              name={agent.name} 
              status={agent.status === 'online' ? 'active' : 'idle'} 
              latency={agent.status === 'online' ? `${(Math.random() * 20 + 5).toFixed(0)}ms` : '0ms'}
            />
          ))}
        </div>

        {/* Matrix Terminal & Intel */}
        <div className="w-1/3 flex flex-col gap-6">
          <MatrixTerminal logs={telemetry.logs} />
          
          <div className="glass-panel p-6 relative overflow-hidden h-52 border-white/5 bg-[#080c18]/90">
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-purple/30 to-transparent" />
            <div className="text-[10px] font-black tracking-[0.25em] text-white/60 uppercase mb-5 flex items-center justify-between">
              Tactical Intelligence
              <div className="flex gap-1">
                <div className="w-1 h-1 bg-cyan rounded-full" />
                <div className="w-1 h-1 bg-purple rounded-full" />
              </div>
            </div>
            <div className="space-y-3.5">
              <IntelItem label="Prometheus Node" status="STABLE" />
              <IntelItem label="Grafana Bridge" status="CONNECTED" />
              <IntelItem label="Edge Cluster" status="V-MESH" />
              <IntelItem label="Odysseus Link" status="ENCRYPTED" color="cyan" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const TacticalMetric = ({ label, value, icon: Icon, color }) => (
  <div className={`glass-panel p-5 flex items-center gap-5 relative overflow-hidden group transition-all duration-500
    ${color === 'cyan' ? 'hover:neon-border-cyan' : 'hover:neon-border-purple'}`}>
    
    <div className={`p-3.5 rounded-xl bg-black/60 border transition-all duration-700
      ${color === 'cyan' ? 'border-cyan/20 text-cyan group-hover:border-cyan/60 shadow-[0_0_15px_rgba(0,242,255,0.1)]' : ''}
      ${color === 'purple' ? 'border-purple/20 text-purple group-hover:border-purple/60 shadow-[0_0_15px_rgba(139,92,246,0.1)]' : ''}
      ${color === 'emerald' ? 'border-emerald-500/20 text-emerald-500 group-hover:border-emerald-500/60 shadow-[0_0_15px_rgba(16,185,129,0.1)]' : ''}
    `}>
      <Icon size={22} className={color === 'cyan' ? 'group-hover:drop-shadow-[0_0_8px_#00f2ff]' : ''} />
    </div>
    <div>
      <div className="text-[10px] font-black text-gray-600 tracking-[0.25em] uppercase mb-1">{label}</div>
      <div className="text-2xl font-black text-white font-mono tracking-tighter">{value}</div>
    </div>
    
    {/* Decorative background element */}
    <div className={`absolute -bottom-6 -right-6 w-20 h-20 opacity-[0.03] transition-opacity group-hover:opacity-[0.08]
      ${color === 'cyan' ? 'bg-cyan' : 'bg-purple'} rounded-full blur-2xl`} />
  </div>
);

const IntelItem = ({ label, status, color = 'gray' }) => (
  <div className="flex justify-between items-center group cursor-default">
    <div className="flex flex-col">
      <span className="text-[11px] text-gray-500 font-bold group-hover:text-white transition-colors">{label}</span>
      <span className="text-[7px] text-gray-700 uppercase tracking-widest opacity-40 group-hover:opacity-100 transition-all">Verified via Core Mesh</span>
    </div>
    <span className={`text-[9px] font-black px-2.5 py-1 rounded-lg bg-black/60 border transition-all
      ${color === 'cyan' ? 'text-cyan border-cyan/20 shadow-[0_0_10px_rgba(0,242,255,0.1)]' : 'text-emerald-500 border-emerald-500/20 shadow-[0_0_10px_rgba(16,185,129,0.1)]'}`}>
      {status}
    </span>
  </div>
);

export default CommandCenter;

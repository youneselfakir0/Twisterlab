import React, { useState, useEffect } from 'react';
import { useTelemetry } from '../hooks/useTelemetry';
import toast from 'react-hot-toast';
import { 
  Cpu, Shield, Zap, Activity, Power, RefreshCw, 
  Terminal, BarChart3, Binary, HardDrive, Network
} from 'lucide-react';

const FleetRegistry = () => {
  const { telemetry, isConnected } = useTelemetry();
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState(null);

  const fetchAgents = async () => {
    setLoading(true);
    try {
      const r = await fetch('/api/v1/agents/live');
      if (r.ok) {
        const data = await r.json();
        setAgents(data);
      }
    } catch (e) {
      console.error("Failed to fetch agents", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAgents();
  }, []);

  const handleToggle = async (agentId, currentStatus) => {
    const isNowActive = currentStatus === 'online';
    const nextActiveState = !isNowActive;
    const loadingToast = toast.loading(`${nextActiveState ? 'Deploying' : 'Terminating'} ${agentId}...`);
    
    try {
      const r = await fetch('/api/v1/agents/toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_id: agentId, active: nextActiveState })
      });
      
      if (r.ok) {
        toast.success(`Agent ${agentId} hot-swapped`, { id: loadingToast });
        setAgents(prev => prev.map(a => a.id === agentId ? { ...a, status: nextActiveState ? 'online' : 'standby' } : a));
      } else {
        throw new Error('Kernel refused agent state change');
      }
    } catch (e) {
      toast.error(`Error: ${e.message}`, { id: loadingToast });
    }
  };

  return (
    <div className="flex flex-1 gap-6 min-h-0 animate-fade-in relative z-10 overflow-hidden">
      
      {/* Left: Tactical Asset List */}
      <div className="flex-1 flex flex-col gap-6 min-w-0">
        <div className="flex items-center justify-between shrink-0">
          <div>
            <h2 className="text-2xl font-black tracking-tighter text-white flex items-center gap-3 uppercase italic">
              <Binary className="text-cyan w-7 h-7" />
              Tactical Asset Management
            </h2>
            <p className="text-gray-500 text-[10px] font-bold uppercase tracking-[0.2em] mt-1">
              Cluster Node: <span className="text-cyan">EDGESERVER-OPS</span> | Protocol: <span className="text-purple">v4.2.1-SECURE</span>
            </p>
          </div>
          
          <div className="flex gap-4">
            <MetricSmall label="Fleet Capacity" value={`${telemetry?.activeAgents || 0}/${telemetry?.totalAgents || 20}`} />
            <button 
              onClick={fetchAgents}
              className="p-3 glass-panel hover:bg-white/5 text-gray-400 hover:text-cyan transition-all rounded-xl"
            >
              <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 pb-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.isArray(agents) && agents.map((agent) => (
              <div 
                key={agent?.id} 
                onClick={() => setSelectedAgent(agent)}
                className={`glass-panel p-4 cursor-pointer transition-all relative group
                  ${selectedAgent?.id === agent?.id ? 'neon-border-cyan' : 'hover:border-white/20'}
                  ${agent?.status === 'online' ? '' : 'opacity-60'}`}
              >
                <div className="flex justify-between items-start mb-4">
                  <div className={`p-2 rounded-lg bg-black/40 border ${agent?.status === 'online' ? 'border-cyan/30 text-cyan shadow-[0_0_10px_rgba(0,242,255,0.2)]' : 'border-white/5 text-gray-600'}`}>
                    <AgentIcon id={agent?.id} />
                  </div>
                  <button 
                    onClick={(e) => { e.stopPropagation(); handleToggle(agent?.id, agent?.status); }}
                    className={`w-8 h-8 flex items-center justify-center rounded-full border transition-all
                      ${agent?.status === 'online' ? 'bg-cyan border-cyan text-black' : 'border-white/20 text-gray-600 hover:text-white hover:border-white'}`}
                  >
                    <Power size={14} />
                  </button>
                </div>
                
                <h3 className="font-black text-white text-xs uppercase tracking-wider mb-1 truncate">{agent?.name}</h3>
                <div className="text-[9px] text-gray-600 font-mono mb-4">ID: {agent?.id}</div>
                
                <div className="flex justify-between items-center pt-3 border-t border-white/5">
                  <div className="flex items-center gap-2">
                    <div className={`w-1.5 h-1.5 rounded-full ${agent?.status === 'online' ? 'bg-emerald-500 animate-pulse' : 'bg-gray-800'}`} />
                    <span className="text-[9px] font-black uppercase text-gray-500 tracking-widest">{agent?.status}</span>
                  </div>
                  <div className="text-[8px] font-mono text-cyan/50 px-1.5 py-0.5 rounded bg-cyan/5 border border-cyan/10">v4.0.2</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right: Detailed Intelligence Panel */}
      <div className="w-96 flex flex-col gap-6 shrink-0 h-full">
        {selectedAgent ? (
          <div className="glass-panel flex-1 flex flex-col overflow-hidden animate-slide-in-right">
            <div className="p-6 border-b border-white/5 bg-white/5">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-3 rounded-xl bg-cyan/10 border border-cyan/30 text-cyan">
                  <AgentIcon id={selectedAgent.id} size={24} />
                </div>
                <div>
                  <h3 className="text-lg font-black text-white uppercase italic">{selectedAgent.name}</h3>
                  <span className="text-[10px] text-cyan font-mono tracking-widest uppercase">Class: {selectedAgent.id.split('-')[0]} Unit</span>
                </div>
              </div>
              <p className="text-xs text-gray-400 leading-relaxed font-medium">
                {selectedAgent.description || "No tactical briefing available for this unit."}
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-8 scrollbar-hide text-white">
              <div>
                <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                  <Activity size={12} className="text-cyan" /> Registered Capabilities
                </h4>
                <div className="flex flex-wrap gap-2">
                  {selectedAgent.capabilities?.map((cap, i) => (
                    <span key={i} className="px-3 py-1.5 bg-black/40 border border-white/10 rounded-lg text-[10px] font-mono text-gray-300">
                      {cap}
                    </span>
                  ))}
                  {(!selectedAgent.capabilities || selectedAgent.capabilities.length === 0) && (
                    <span className="text-[10px] text-gray-700 italic">No autonomous tools registered</span>
                  )}
                </div>
              </div>

              <div>
                <h4 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                  <BarChart3 size={12} className="text-purple" /> Resource Allocation
                </h4>
                <div className="space-y-4">
                  <ResourceGauge label="Neural compute" value={selectedAgent.status === 'online' ? 24 : 0} color="cyan" />
                  <ResourceGauge label="Memory Buffer" value={selectedAgent.status === 'online' ? 12 : 0} color="purple" />
                </div>
              </div>

              <div className="p-4 rounded-xl bg-purple/5 border border-purple/20">
                <h4 className="text-[10px] font-black text-purple-400 uppercase tracking-widest mb-2 flex items-center gap-2">
                  <Shield size={12} /> Security Clearance
                </h4>
                <div className="text-[9px] text-purple-400/70 font-mono leading-relaxed">
                  Unit authorized for Level 3 infrastructure access. All operations logged in Matrix.
                </div>
              </div>
            </div>
            
            <div className="p-4 bg-black/40 border-t border-white/5">
              <button className="w-full py-3 bg-white/5 border border-white/10 rounded-lg text-[10px] font-black uppercase tracking-[0.2em] text-gray-500 cursor-not-allowed">
                Hot-Swap Core (Locked)
              </button>
            </div>
          </div>
        ) : (
          <div className="glass-panel flex-1 flex flex-col items-center justify-center text-center p-12 opacity-40">
            <Terminal size={48} className="text-gray-700 mb-6" />
            <h3 className="text-sm font-black text-white uppercase tracking-widest mb-2 text-white">Asset Intel Offline</h3>
            <p className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Select a tactical unit to view capabilities</p>
          </div>
        )}

        <div className="glass-panel p-5 h-40 relative overflow-hidden shrink-0">
          <div className="scanline" />
          <h4 className="text-[10px] font-black text-white/50 uppercase tracking-widest mb-4">Fleet Status</h4>
          <div className="space-y-3">
            <StatusItem icon={Network} label="MCP Mesh" status="STABLE" />
            <StatusItem icon={HardDrive} label="Storage" status="OPTIMAL" />
          </div>
        </div>
      </div>
    </div>
  );
};

const AgentIcon = ({ id, size = 18 }) => {
  const nid = (id || '').toLowerCase();
  if (nid.includes('monitoring') || nid.includes('health')) return <Activity size={size} />;
  if (nid.includes('shield') || nid.includes('sec')) return <Shield size={size} />;
  if (nid.includes('zap') || nid.includes('trade')) return <Zap size={size} />;
  if (nid.includes('maestro') || nid.includes('brain')) return <Binary size={size} />;
  return <Cpu size={size} />;
};

const MetricSmall = ({ label, value }) => (
  <div className="glass-panel px-4 py-2 flex flex-col items-end">
    <span className="text-[9px] text-gray-500 uppercase font-black tracking-widest">{label}</span>
    <span className="text-xl font-bold text-cyan font-mono">{value}</span>
  </div>
);

const ResourceGauge = ({ label, value, color }) => (
  <div>
    <div className="flex justify-between text-[9px] font-bold text-gray-500 uppercase mb-1.5">
      <span>{label}</span>
      <span className="text-white font-mono">{value}%</span>
    </div>
    <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
      <div 
        className={`h-full transition-all duration-1000 ${color === 'cyan' ? 'bg-cyan shadow-[0_0_8px_#00f2ff]' : 'bg-purple shadow-[0_0_8px_#8b5cf6]'}`} 
        style={{ width: `${value}%` }} 
      />
    </div>
  </div>
);

const StatusItem = ({ icon: Icon, label, status }) => (
  <div className="flex justify-between items-center text-white">
    <div className="flex items-center gap-2">
      <Icon size={12} className="text-cyan" />
      <span className="text-[10px] font-bold text-gray-500 uppercase">{label}</span>
    </div>
    <span className="text-[9px] font-mono text-emerald-500 font-black tracking-widest">{status}</span>
  </div>
);

export default FleetRegistry;

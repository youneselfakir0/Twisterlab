import React, { useState, useEffect, useRef } from 'react';
import { useTelemetry } from '../hooks/useTelemetry';
import { 
  Send, Terminal, Sparkles, Activity, Shield, Cpu, Zap, Brain, Play, Eye, 
  CheckCircle2, XCircle, Clock, ArrowRight, Search, AlertTriangle, 
  ChevronDown, ChevronUp, RefreshCw, BarChart2, Check, UserCheck, HelpCircle,
  Book
} from 'lucide-react';
import toast from 'react-hot-toast';

const MaestroAI = () => {
  const { telemetry, isConnected } = useTelemetry();
  const [prompt, setPrompt] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState('');
  const [activeView, setActiveView] = useState('console');
  const [fleet, setFleet] = useState([]);
  const [dryRunResult, setDryRunResult] = useState(null);
  const [missionResult, setMissionResult] = useState(null);
  const [executionSteps, setExecutionSteps] = useState([]);
  const [expandedSteps, setExpandedSteps] = useState({});
  const [missionHistory, setMissionHistory] = useState([]);

  const [consoleLogs, setConsoleLogs] = useState([
    { timestamp: new Date().toLocaleTimeString(), type: 'system', text: 'Maestro Orchestrator Brain online. System registry synced.' },
    { timestamp: new Date().toLocaleTimeString(), type: 'system', text: 'Standing by for multi-agent dispatch.' }
  ]);
  const consoleEndRef = useRef(null);

  useEffect(() => {
    fetchFleet();
    fetchMissionHistory();
  }, []);

  useEffect(() => {
    consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [consoleLogs]);

  const fetchFleet = async () => {
    try {
      const r = await fetch('/api/v1/agents/live');
      if (r.ok) {
        const data = await r.json();
        setFleet(data);
      }
    } catch (err) {
      console.error('Error fetching fleet:', err);
    }
  };

  const fetchMissionHistory = async () => {
    try {
      const r = await fetch('/api/v1/maestro/missions');
      if (r.ok) {
        const data = await r.json();
        setMissionHistory(data.missions || []);
      }
    } catch (err) {
      console.error('Error fetching missions:', err);
    }
  };

  const loadMissionDetail = async (missionId) => {
    const loadingToast = toast.loading(`Loading trace ${missionId}...`);
    try {
      const r = await fetch(`/api/v1/maestro/missions/${missionId}`);
      if (r.ok) {
        const data = await r.json();
        setMissionResult(data);
        setExecutionSteps(data.results || []);
        setActiveView('synthesis');
        toast.success('Trace loaded', { id: loadingToast });
      }
    } catch (err) {
      toast.error('Failed to load trace', { id: loadingToast });
    }
  };

  const addLog = (text, type = 'info') => {
    setConsoleLogs(prev => [...prev, {
      timestamp: new Date().toLocaleTimeString(),
      type,
      text
    }]);
  };

  const toggleStepExpand = (stepId) => {
    setExpandedSteps(prev => ({
      ...prev,
      [stepId]: !prev[stepId]
    }));
  };

  const handleAction = async (e, mode) => {
    e.preventDefault();
    if (!prompt.trim() || isProcessing) return;

    const userMsg = prompt.trim();
    setIsProcessing(true);
    setDryRunResult(null);
    setMissionResult(null);
    setExecutionSteps([]);
    
    const isDryRun = mode === 'dry_run';
    addLog(`Operator command: "${userMsg}" [${isDryRun ? 'DRY RUN' : 'LIVE'}]`, 'operator');
    
    const loadingToast = toast.loading(isDryRun ? 'Generating tactical plan...' : 'Orchestrating agent fleet...');

    try {
      const r = await fetch('/api/v1/mcp/tools/orchestrate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task: userMsg, context: { dry_run: isDryRun } })
      });

      if (!r.ok) throw new Error(`HTTP error! status: ${r.status}`);
      const envelope = await r.json();
      const rawText = envelope.content?.[0]?.text || '{}';
      const responseData = JSON.parse(rawText);

      if (responseData.mode === 'chat') {
        addLog(responseData.response, 'maestro');
        toast.success('Response received', { id: loadingToast });
      } else if (isDryRun) {
        setDryRunResult(responseData);
        setActiveView('planner');
        addLog(responseData.thought || 'Plan compiled.', 'maestro');
        toast.success('Plan Generated', { id: loadingToast });
      } else {
        setMissionResult(responseData);
        setExecutionSteps(responseData.results || []);
        setActiveView('synthesis');
        addLog(responseData.thought || 'Mission complete.', 'maestro');
        toast.success('Mission Complete', { id: loadingToast });
        fetchMissionHistory(); // Refresh history
      }
    } catch (err) {
      addLog(`Error: ${err.message}`, 'error');
      toast.error(`Error: ${err.message}`, { id: loadingToast });
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col gap-6 overflow-hidden relative">
      <div className="scanline" />
      
      {/* Top HUD */}
      <div className="glass-panel p-6 flex items-center justify-between relative overflow-hidden shrink-0">
        <div className="flex items-center gap-6">
          <div className={`w-14 h-14 rounded-xl border flex items-center justify-center transition-all duration-700
            ${isProcessing ? 'border-purple shadow-[0_0_20px_rgba(139,92,246,0.4)] bg-purple/10' : 'border-cyan/30 bg-cyan/5'}
          `}>
            {isProcessing ? <Brain className="text-purple animate-pulse" size={32} /> : <Brain className="text-cyan" size={32} />}
          </div>
          <div>
            <h2 className="text-2xl font-black text-white tracking-tighter uppercase italic">Maestro Orchestrator</h2>
            <div className="flex items-center gap-3 mt-1">
              <span className="flex items-center gap-1.5 text-[10px] font-bold text-cyan tracking-widest uppercase">
                <Activity size={12} className={isProcessing ? 'animate-spin' : 'animate-pulse'} /> 
                {isProcessing ? 'Thinking...' : 'Neural Link Active'}
              </span>
              <span className="text-gray-500 text-[10px] font-mono">NODE: EDGESERVER-OPS</span>
            </div>
          </div>
        </div>
        
        <div className="flex gap-2">
          {['console', 'library', 'planner', 'synthesis'].map(view => (
            <button
              key={view}
              onClick={() => setActiveView(view)}
              disabled={(view === 'planner' || view === 'synthesis') && !dryRunResult && !missionResult}
              className={`px-4 py-2 text-[10px] font-black uppercase tracking-widest border transition-all rounded
                ${activeView === view ? 'bg-cyan/10 border-cyan text-cyan shadow-[0_0_10px_rgba(0,242,255,0.2)]' : 'border-white/5 text-gray-500 hover:text-white disabled:opacity-20'}
              `}
            >
              {view}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex gap-6 min-h-0">
        {/* Main Workstation */}
        <div className="flex-1 flex flex-col glass-panel overflow-hidden relative">
          <div className="flex-1 overflow-y-auto p-6 scrollbar-hide">
            {activeView === 'console' && (
              <div className="space-y-3 font-mono text-[11px]">
                {consoleLogs.map((log, i) => (
                  <div key={i} className="flex gap-3 p-1 hover:bg-white/5 transition-colors">
                    <span className="text-gray-700">[{log.timestamp}]</span>
                    <span className={`font-bold ${
                      log.type === 'operator' ? 'text-amber-500' : 
                      log.type === 'maestro' ? 'text-cyan' : 
                      log.type === 'error' ? 'text-red-500' : 'text-purple-400'
                    }`}>{log.type.toUpperCase()}:</span>
                    <span className="text-gray-300">{log.text}</span>
                  </div>
                ))}
                <div ref={consoleEndRef} />
              </div>
            )}

            {activeView === 'library' && (
              <div className="space-y-4">
                <div className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] mb-4">Mission Archives</div>
                {missionHistory.length === 0 ? (
                  <div className="text-center py-20 opacity-30">
                    <Book size={48} className="mx-auto mb-4" />
                    <p className="text-[10px] uppercase tracking-widest font-black">Archive Empty</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 gap-3">
                    {missionHistory.map((m) => (
                      <div 
                        key={m.id} 
                        onClick={() => loadMissionDetail(m.id)}
                        className="p-4 bg-white/5 border border-white/5 rounded-xl hover:border-cyan/40 cursor-pointer transition-all group"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <span className="text-[9px] font-mono text-cyan/60">{m.id}</span>
                          <span className="text-[9px] font-mono text-gray-600">{new Date(m.completed_at).toLocaleString()}</span>
                        </div>
                        <h4 className="text-xs font-bold text-white uppercase truncate group-hover:text-cyan transition-colors">{m.task}</h4>
                        <p className="text-[10px] text-gray-500 mt-2 line-clamp-1">{m.summary}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {activeView === 'planner' && (dryRunResult || missionResult) && (
              <div className="space-y-6">
                <div className="flex gap-4 p-4 bg-white/5 border border-white/5 rounded-lg">
                  <div className="flex-1">
                    <span className="text-[9px] text-gray-500 font-black uppercase block mb-1">Tactical Category</span>
                    <span className="text-xs font-bold text-cyan uppercase">{dryRunResult?.analysis?.category || missionResult?.analysis?.category}</span>
                  </div>
                  <div className="flex-1">
                    <span className="text-[9px] text-gray-500 font-black uppercase block mb-1">Priority Level</span>
                    <span className="text-xs font-bold text-purple uppercase">{dryRunResult?.analysis?.priority || missionResult?.analysis?.priority}</span>
                  </div>
                </div>
                
                <div className="space-y-4">
                  {(dryRunResult?.plan?.steps || missionResult?.steps || []).map((step, i) => (
                    <div key={i} className="p-4 bg-black/40 border border-white/5 rounded-xl group hover:border-cyan/30 transition-all">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-3">
                          <span className="text-[10px] font-mono text-gray-600">0{i+1}</span>
                          <span className="text-xs font-bold text-white uppercase">{step.agent}</span>
                        </div>
                        <span className="text-[9px] font-mono text-cyan/70">{step.capability}</span>
                      </div>
                      <p className="text-[11px] text-gray-400">{step.purpose}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeView === 'synthesis' && missionResult && (
              <div className="space-y-6">
                <div className="glass-panel p-6 border-cyan/20 bg-cyan/5">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 rounded-full border-2 border-cyan flex items-center justify-center text-lg font-black text-white">
                      {((missionResult.synthesis?.success_rate ?? 1) * 100).toFixed(0)}%
                    </div>
                    <div>
                      <span className="text-[10px] font-black text-cyan uppercase tracking-widest">Mission Synthesis</span>
                      <h3 className="text-sm font-bold text-white">Resolution Summary</h3>
                    </div>
                  </div>
                  <p className="text-xs text-gray-300 leading-relaxed font-mono bg-black/40 p-4 rounded-lg border border-white/5 mb-6">
                    {missionResult.synthesis?.summary}
                  </p>

                  {missionResult.notion_url && (
                    <a 
                      href={missionResult.notion_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center justify-center gap-2 w-full py-3 bg-white/5 border border-white/10 rounded-lg text-[10px] font-black uppercase tracking-[0.2em] text-white hover:bg-white/10 transition-all group"
                    >
                      <Book className="text-cyan group-hover:animate-pulse" size={14} />
                      View Mission Log in Notion
                    </a>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Input Area */}
          <form onSubmit={(e) => handleAction(e, 'execute')} className="p-4 bg-black/40 border-t border-white/5">
            <div className="flex gap-3">
              <div className="flex-1 relative">
                <input 
                  type="text"
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  disabled={isProcessing}
                  placeholder="Dispatch tactical command..."
                  className="w-full bg-white/5 border border-white/5 rounded-lg px-4 py-3 text-xs text-white focus:outline-none focus:border-cyan/40 transition-all font-mono"
                />
                <Terminal className="absolute right-4 top-3.5 text-gray-700" size={14} />
              </div>
              <button 
                type="button"
                onClick={(e) => handleAction(e, 'dry_run')}
                disabled={isProcessing || !prompt.trim()}
                className="px-6 py-3 border border-cyan/30 text-cyan text-[10px] font-black uppercase tracking-widest rounded-lg hover:bg-cyan/10 transition-all"
              >
                Plan
              </button>
              <button 
                type="submit"
                disabled={isProcessing || !prompt.trim()}
                className="px-6 py-3 bg-cyan text-black text-[10px] font-black uppercase tracking-widest rounded-lg hover:bg-cyan/80 transition-all shadow-[0_0_15px_rgba(0,242,255,0.3)]"
              >
                Execute
              </button>
            </div>
          </form>
        </div>

        {/* Sidebar: Analytics/Intel */}
        <div className="w-80 flex flex-col gap-6 shrink-0">
          <div className="glass-panel p-5 flex-1 overflow-hidden flex flex-col">
            <h3 className="text-[10px] font-black text-white uppercase tracking-widest mb-4 flex items-center gap-2">
              <Zap size={12} className="text-cyan" /> Unit Intelligence
            </h3>
            <div className="flex-1 overflow-y-auto space-y-4 scrollbar-hide">
              {fleet.map((agent, i) => (
                <div key={i} className="p-3 bg-black/40 border border-white/5 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-bold text-gray-300 uppercase">{agent.name}</span>
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_5px_#10b981]" />
                  </div>
                  <p className="text-[10px] text-gray-500 line-clamp-2">{agent.description}</p>
                </div>
              ))}
            </div>
          </div>
          
          <div className="glass-panel p-5 h-48 bg-purple/5 border-purple/20 relative overflow-hidden">
            <div className="scanline opacity-[0.02]" />
            <h3 className="text-[10px] font-black text-purple-400 uppercase tracking-widest mb-4">Neural Performance</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-end">
                <span className="text-[10px] text-gray-500 font-bold">LATENCY (P95)</span>
                <span className="text-xs font-mono text-white">124ms</span>
              </div>
              <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-purple w-2/3 shadow-[0_0_8px_#8b5cf6]" />
              </div>
              <div className="flex justify-between items-end">
                <span className="text-[10px] text-gray-500 font-bold">ACCURACY</span>
                <span className="text-xs font-mono text-white">99.4%</span>
              </div>
              <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
                <div className="h-full bg-cyan w-[99.4%] shadow-[0_0_8px_#00f2ff]" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MaestroAI;

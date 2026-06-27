import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { 
  Shield, Cpu, Network, Zap, Lock, Eye, EyeOff, Save, RefreshCw, 
  Database, Server, Bell, Monitor, Globe, Binary
} from 'lucide-react';

const Settings = () => {
  const [activeTab, setActiveTab] = useState('system');
  const [isSaving, setIsSaving] = useState(false);
  const [showTokens, setShowTokens] = useState(false);
  
  // State for different categories
  const [systemConfig, setSystemConfig] = useState({
    apiUrl: '192.168.0.30:8000',
    refreshRate: localStorage.getItem('twister_refresh_rate') || '5000',
    debugMode: false,
    telemetryEnabled: true
  });

  const [aiConfig, setAiConfig] = useState({
    defaultModel: 'llama3.2:1b',
    cortexUrl: 'http://192.168.0.20:11434',
    odysseusUrl: 'http://192.168.0.30:7000',
    temperature: 0.7,
    maxTokens: 2048
  });

  const [securityConfig, setSecurityConfig] = useState({
    mcpToken: '',
    notionToken: '',
    githubToken: '',
    encryptionLevel: 'AES-256-GCM'
  });

  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('twister_jwt');
    if (token) setIsAuthenticated(true);
  }, []);

  const handleLogin = () => {
    const t = toast.loading('Authenticating session...');
    setTimeout(() => {
      localStorage.setItem('twister_jwt', 'odt_session_active');
      setIsAuthenticated(true);
      toast.success('Access Granted — Welcome to Odysseus Edition', { id: t });
    }, 800);
  };

  const handleSaveAll = async () => {
    setIsSaving(true);
    const t = toast.loading('Syncing parameters to core infrastructure...');
    
    // Simulate API call
    await new Promise(r => setTimeout(r, 1500));
    
    localStorage.setItem('twister_refresh_rate', systemConfig.refreshRate);
    toast.success('Configuration synchronized and persistent.', { id: t });
    setIsSaving(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-6">
        <div className="glass-panel neon-border-cyan rounded-2xl p-10 max-w-md w-full text-center relative overflow-hidden">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan to-transparent opacity-50" />
          <div className="w-20 h-20 bg-cyan/10 rounded-full flex items-center justify-center mx-auto mb-6 border border-cyan/20">
            <Lock size={32} className="text-cyan drop-shadow-[0_0_8px_#00f2ff]" />
          </div>
          <div className="text-[14px] font-black tracking-[0.3em] uppercase text-white mb-2">Security Override Required</div>
          <div className="text-[11px] text-gray-400 mb-8 leading-relaxed font-medium">
            Access to Odysseus Core Configuration is restricted. <br/>
            Please authorize your session to proceed.
          </div>
          <button 
            onClick={handleLogin}
            className="w-full bg-cyan hover:bg-cyan-glow text-black font-black text-[11px] px-6 py-4 rounded-xl tracking-[0.2em] transition-all shadow-[0_0_20px_rgba(0,242,255,0.2)]"
          >
            AUTHORIZE PROTOCOL
          </button>
        </div>
      </div>
    );
  }

  const tabs = [
    { id: 'system', label: 'System', icon: Monitor },
    { id: 'ai', label: 'AI Engine', icon: Cpu },
    { id: 'mcp', label: 'MCP Servers', icon: Network },
    { id: 'security', label: 'Security', icon: Shield },
  ];

  return (
    <div className="flex flex-col flex-1 min-h-0 glass-panel rounded-2xl overflow-hidden border-white/5 shadow-2xl">
      {/* Settings Header */}
      <div className="flex items-center px-8 py-6 border-b border-white/5 bg-white/[0.02]">
        <div className="flex-1">
          <div className="text-[12px] font-black tracking-[0.25em] text-white uppercase flex items-center gap-3">
            <Settings size={18} className="text-cyan" />
            Core Infrastructure Settings
          </div>
          <div className="text-[10px] text-gray-500 font-bold tracking-wider mt-1 uppercase">TwisterLab v4.2 // Odysseus Integrated</div>
        </div>
        <button 
          onClick={handleSaveAll}
          disabled={isSaving}
          className="bg-cyan/10 hover:bg-cyan/20 border border-cyan/30 text-cyan px-6 py-2.5 rounded-xl text-[10px] font-black tracking-widest transition-all flex items-center gap-2"
        >
          {isSaving ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
          {isSaving ? 'SYNCING...' : 'COMMIT CHANGES'}
        </button>
      </div>

      <div className="flex flex-1 min-h-0">
        {/* Sub-navigation */}
        <div className="w-56 border-r border-white/5 bg-black/20 py-6">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`w-full flex items-center gap-4 px-8 py-4 text-[11px] font-bold transition-all relative
                ${activeTab === tab.id ? 'text-white' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'}`}
            >
              {activeTab === tab.id && <div className="absolute left-0 top-0 bottom-0 w-1 bg-cyan shadow-[0_0_15px_#00f2ff]" />}
              <tab.icon size={16} className={activeTab === tab.id ? 'text-cyan' : ''} />
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content Area */}
        <div className="flex-1 p-10 overflow-y-auto bg-black/10">
          {activeTab === 'system' && (
            <div className="max-w-2xl space-y-8 animate-in fade-in slide-in-from-bottom-2">
              <SectionHeader title="Infrastructure Parameters" />
              <div className="grid grid-cols-2 gap-6">
                <InputGroup label="API Gateway URL" value={systemConfig.apiUrl} readOnly icon={Globe} />
                <SelectGroup 
                  label="Telemetry Refresh" 
                  value={systemConfig.refreshRate} 
                  options={[
                    { label: 'Aggressive (2s)', value: '2000' },
                    { label: 'Standard (5s)', value: '5000' },
                    { label: 'Relaxed (15s)', value: '15000' }
                  ]}
                  onChange={v => setSystemConfig({...systemConfig, refreshRate: v})}
                />
              </div>
              <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5">
                <Toggle label="Advanced Debug Mode" description="Enables verbose logging in the Matrix Terminal." active={systemConfig.debugMode} onToggle={() => setSystemConfig({...systemConfig, debugMode: !systemConfig.debugMode})} />
              </div>
            </div>
          )}

          {activeTab === 'ai' && (
            <div className="max-w-2xl space-y-8 animate-in fade-in slide-in-from-bottom-2">
              <SectionHeader title="Neural Engine Configuration" />
              <div className="space-y-6">
                <InputGroup label="Cortex LLM Node" value={aiConfig.cortexUrl} icon={Server} />
                <InputGroup label="Odysseus Workspace Node" value={aiConfig.odysseusUrl} icon={Binary} />
                <div className="grid grid-cols-2 gap-6 pt-4">
                  <SelectGroup 
                    label="Primary Model Selection" 
                    value={aiConfig.defaultModel} 
                    options={[
                      { label: 'Llama 3.2 (Fast)', value: 'llama3.2:1b' },
                      { label: 'Mistral (Balanced)', value: 'mistral' },
                      { label: 'Odysseus-Vision (Expert)', value: 'odysseus-vision' }
                    ]}
                  />
                  <div>
                    <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.15em] block mb-3">Response Temperature</label>
                    <input type="range" className="w-full accent-cyan" min="0" max="1" step="0.1" value={aiConfig.temperature} onChange={e => setAiConfig({...aiConfig, temperature: parseFloat(e.target.value)})} />
                    <div className="flex justify-between text-[9px] text-gray-600 font-bold mt-2">
                      <span>PRECISE</span>
                      <span className="text-cyan">{aiConfig.temperature}</span>
                      <span>CREATIVE</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'mcp' && (
            <div className="max-w-3xl space-y-8 animate-in fade-in slide-in-from-bottom-2">
              <div className="flex justify-between items-center">
                <SectionHeader title="Model Context Protocol (MCP) Servers" />
                <button className="bg-purple/10 border border-purple/30 text-purple text-[9px] font-black px-3 py-1.5 rounded-lg uppercase tracking-wider hover:bg-purple/20 transition-all">+ Add Server</button>
              </div>
              <div className="space-y-4">
                <McpServerItem name="Twister-Internal-Tools" type="SSE" url="http://192.168.0.30:30000/api/v1/mcp/sse" status="online" tools={12} />
                <McpServerItem name="FileSystem-Access" type="STDIO" url="npx -y @modelcontextprotocol/server-filesystem /app/data" status="offline" tools={0} />
              </div>
            </div>
          )}

          {activeTab === 'security' && (
            <div className="max-w-2xl space-y-8 animate-in fade-in slide-in-from-bottom-2">
              <div className="flex justify-between items-center">
                <SectionHeader title="Credential Vault & Zero-Trust" />
                <button 
                  onClick={() => setShowTokens(!showTokens)}
                  className="text-[10px] font-black text-gray-500 hover:text-white flex items-center gap-2 transition-colors uppercase tracking-widest"
                >
                  {showTokens ? <EyeOff size={14} /> : <Eye size={14} />}
                  {showTokens ? 'Hide Secrets' : 'Reveal Secrets'}
                </button>
              </div>
              <div className="space-y-6">
                <TokenInput label="MCP Authorization Key" value={securityConfig.mcpToken} show={showTokens} placeholder="odt_..." />
                <TokenInput label="Notion Integration Secret" value={securityConfig.notionToken} show={showTokens} placeholder="secret_..." />
                <TokenInput label="GitHub Personal Access Token" value={securityConfig.githubToken} show={showTokens} placeholder="ghp_..." />
              </div>
              <div className="p-4 rounded-xl bg-cyan/5 border border-cyan/20 flex gap-4 items-center mt-8">
                <Lock size={20} className="text-cyan" />
                <div className="text-[10px] text-cyan/80 font-medium leading-relaxed uppercase tracking-wider">
                  All keys are encrypted using <span className="text-white font-bold">{securityConfig.encryptionLevel}</span> and stored in the local cluster vault.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const SectionHeader = ({ title }) => (
  <div className="text-[11px] font-black text-white uppercase tracking-[0.2em] mb-6">{title}</div>
);

const InputGroup = ({ label, value, readOnly, icon: Icon }) => (
  <div>
    <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.15em] block mb-3">{label}</label>
    <div className="relative">
      {Icon && <Icon size={14} className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-600" />}
      <input 
        type="text" 
        value={value} 
        readOnly={readOnly}
        className={`w-full bg-white/[0.03] border border-white/10 rounded-xl py-3 text-sm text-gray-300 outline-none focus:border-cyan/50 transition-all ${Icon ? 'pl-12' : 'px-4'} ${readOnly ? 'opacity-60' : ''}`} 
      />
    </div>
  </div>
);

const SelectGroup = ({ label, value, options, onChange }) => (
  <div>
    <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.15em] block mb-3">{label}</label>
    <select 
      value={value} 
      onChange={e => onChange?.(e.target.value)}
      className="w-full bg-white/[0.03] border border-white/10 rounded-xl px-4 py-3 text-sm text-gray-300 outline-none focus:border-cyan/50 transition-all cursor-pointer"
    >
      {options.map(o => <option key={o.value} value={o.value} className="bg-[#080c18] text-white">{o.label}</option>)}
    </select>
  </div>
);

const TokenInput = ({ label, value, show, placeholder }) => (
  <div>
    <label className="text-[10px] font-black text-gray-500 uppercase tracking-[0.15em] block mb-3">{label}</label>
    <input 
      type={show ? 'text' : 'password'} 
      value={value} 
      className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-sm font-mono text-cyan outline-none focus:border-cyan/50 transition-all" 
      placeholder={placeholder}
    />
  </div>
);

const Toggle = ({ label, description, active, onToggle }) => (
  <div className="flex items-center justify-between">
    <div>
      <div className="text-[11px] font-bold text-white uppercase tracking-wider mb-1">{label}</div>
      <div className="text-[10px] text-gray-500 font-medium">{description}</div>
    </div>
    <button 
      onClick={onToggle}
      className={`w-12 h-6 rounded-full relative transition-all ${active ? 'bg-cyan shadow-[0_0_10px_rgba(0,242,255,0.4)]' : 'bg-white/10'}`}
    >
      <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${active ? 'left-7' : 'left-1'}`} />
    </button>
  </div>
);

const McpServerItem = ({ name, type, url, status, tools }) => (
  <div className="p-4 rounded-xl bg-white/[0.02] border border-white/5 flex items-center gap-4 hover:border-white/10 transition-all">
    <div className={`w-2 h-2 rounded-full ${status === 'online' ? 'bg-emerald-500 animate-pulse shadow-[0_0_8px_#10b981]' : 'bg-red-500'}`} />
    <div className="flex-1">
      <div className="flex items-center gap-3">
        <span className="text-[11px] font-bold text-white uppercase tracking-wider">{name}</span>
        <span className="text-[9px] bg-white/5 px-2 py-0.5 rounded text-gray-500 font-black">{type}</span>
      </div>
      <div className="text-[10px] text-gray-600 font-mono mt-1 truncate max-w-sm">{url}</div>
    </div>
    <div className="text-right">
      <div className="text-[11px] font-black text-white">{tools}</div>
      <div className="text-[9px] text-gray-500 font-bold uppercase tracking-widest">Tools Found</div>
    </div>
  </div>
);

export default Settings;

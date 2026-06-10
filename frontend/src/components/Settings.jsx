import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

const Settings = () => {
  const [isSaving, setIsSaving] = useState(false);
  const [mcpToken, setMcpToken] = useState('');
  const [notionToken, setNotionToken] = useState('');
  const [n8nUrl, setN8nUrl] = useState('http://192.168.0.30:5678');
  
  // Simulated Authentication & Encryption status
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Load preferences from localStorage
  const [refreshRate, setRefreshRate] = useState(() => {
    return localStorage.getItem('twister_refresh_rate') || '5000';
  });

  useEffect(() => {
    // Check auth status mock
    const token = localStorage.getItem('twister_jwt');
    if (token) setIsAuthenticated(true);
  }, []);

  const handleLogin = () => {
    const t = toast.loading('Authenticating securely...');
    setTimeout(() => {
      localStorage.setItem('twister_jwt', 'mock-encrypted-token');
      setIsAuthenticated(true);
      toast.success('Session Authenticated (Zero Trust Mode)', { id: t });
    }, 1000);
  };

  const handleLogout = () => {
    localStorage.removeItem('twister_jwt');
    setIsAuthenticated(false);
    toast('Session Terminated', { icon: '🔒' });
  };

  const handleSavePreferences = () => {
    localStorage.setItem('twister_refresh_rate', refreshRate);
    toast.success(`Dashboard refresh rate saved: ${refreshRate}ms`);
  };

  const handleSaveSecurity = async () => {
    if (!isAuthenticated) {
      toast.error('Unauthorized. Please authenticate first.');
      return;
    }
    
    setIsSaving(true);
    const t = toast.loading('Encrypting and syncing keys to Kubernetes Vault...');
    
    // Simulate API save
    await new Promise(r => setTimeout(r, 2000));
    
    // Clear sensitive fields locally (Security Hardening)
    setMcpToken('');
    setNotionToken('');
    
    toast.success('Security configuration locked and loaded.', { id: t });
    setIsSaving(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center">
        <div className="bg-panel border border-white/10 rounded-xl p-8 shadow-2xl max-w-md w-full text-center">
          <div className="text-4xl mb-4">🔒</div>
          <div className="text-sm font-bold tracking-widest uppercase text-white mb-2">Zero Trust Authentication</div>
          <div className="text-xs text-gray-400 mb-8 leading-relaxed">
            API keys and critical operations are locked. Please verify your identity to manage infrastructure.
          </div>
          <button 
            onClick={handleLogin}
            className="w-full bg-cyan text-black font-extrabold text-[11px] px-4 py-3 rounded-lg tracking-wider hover:shadow-[0_0_15px_var(--tw-colors-cyan-glow)] transition-all"
          >
            AUTHORIZE SESSION
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-6 flex-1 min-h-0 overflow-y-auto">
      
      {/* Col 1 */}
      <div className="flex flex-col gap-6">
        <div className="bg-panel border border-white/10 rounded-xl shadow-xl p-6">
          <div className="flex justify-between items-center mb-6">
             <div className="text-[11px] font-extrabold tracking-widest text-white uppercase">System Parameters</div>
             <button onClick={handleLogout} className="text-[10px] text-red-500 hover:bg-red-500/10 px-3 py-1 rounded border border-red-500/30 transition-colors">END SESSION</button>
          </div>
          
          <div className="space-y-4">
            <FormGroup label="API Node Address" value="192.168.0.30:8000" readOnly />
            <FormGroup label="System Version" value="v4.0.0 (IT Focused)" readOnly />
            <FormGroup label="Local LLM Engine" value="Ollama (Connected)" readOnly />
          </div>
        </div>

        <div className="bg-panel border border-white/10 rounded-xl shadow-xl p-6">
          <div className="text-[11px] font-extrabold tracking-widest text-white uppercase mb-6">Dashboard Preferences</div>
          
          <div className="space-y-4">
            <div>
              <label className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] block mb-2">Telemetry Refresh Rate</label>
              <select 
                value={refreshRate}
                onChange={e => setRefreshRate(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-white text-sm focus:border-cyan outline-none appearance-none cursor-pointer"
              >
                <option value="2000" className="bg-bg text-white">Aggressive (2s)</option>
                <option value="5000" className="bg-bg text-white">Standard (5s)</option>
                <option value="15000" className="bg-bg text-white">Relaxed (15s)</option>
              </select>
            </div>
            <button 
              onClick={handleSavePreferences}
              className="w-full bg-white/10 hover:bg-white/20 text-white font-extrabold text-[11px] px-4 py-3 rounded-lg tracking-wider transition-all"
            >
              APPLY PREFERENCES
            </button>
          </div>
        </div>
      </div>

      {/* Col 2 */}
      <div className="bg-panel border border-white/10 rounded-xl shadow-xl p-6 flex flex-col">
        <div className="flex justify-between items-center mb-6">
          <div className="text-[11px] font-extrabold tracking-widest text-white uppercase">Platform Governance & Security</div>
          <span className="bg-emerald-500/10 text-emerald-500 px-2 py-1 rounded text-[10px] font-bold">SECURE VAULT</span>
        </div>

        <div className="space-y-4 flex-1">
          <div>
            <label className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] block mb-2">MCP Authorization Token</label>
            <input type="password" value={mcpToken} onChange={e=>setMcpToken(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-white text-sm focus:border-cyan outline-none" placeholder="Enter MCP Token" />
          </div>
          <div>
            <label className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] block mb-2">Notion Integration Token</label>
            <input type="password" value={notionToken} onChange={e=>setNotionToken(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-white text-sm focus:border-cyan outline-none" placeholder="Enter Notion Token" />
          </div>
          <div>
            <label className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] block mb-2">n8n Gateway URL</label>
            <input type="text" value={n8nUrl} onChange={e=>setN8nUrl(e.target.value)} className="w-full bg-white/5 border border-white/10 rounded-lg p-3 text-white text-sm focus:border-cyan outline-none" placeholder="http://..." />
          </div>
        </div>

        <div className="mt-6">
          <button 
            onClick={handleSaveSecurity}
            disabled={isSaving || !n8nUrl}
            className="w-full bg-cyan text-black font-extrabold text-[11px] px-4 py-3 rounded-lg tracking-wider disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-[0_0_15px_var(--tw-colors-cyan-glow)] transition-all flex justify-center items-center gap-2"
          >
            {isSaving ? <span className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" /> : null}
            {isSaving ? 'ENCRYPTING & SAVING...' : 'SAVE SECURITY CONFIG'}
          </button>
        </div>
      </div>

    </div>
  );
};

const FormGroup = ({ label, value }) => (
  <div>
    <label className="text-[10px] font-bold text-gray-500 uppercase tracking-[0.1em] block mb-2">{label}</label>
    <div className="bg-white/5 border border-white/10 rounded-lg p-3 font-mono text-sm text-gray-300">
      {value}
    </div>
  </div>
);

export default Settings;

import React, { useState, useEffect } from 'react';
import { Shield, RefreshCw, CheckCircle, AlertTriangle, Users, Database } from 'lucide-react';
import toast from 'react-hot-toast';

const DomainSyncView = () => {
  const [loading, setLoading] = useState(false);
  const [syncStatus, setSyncStatus] = useState(null);
  const [lastSync, setLastSync] = useState(null);

  const triggerSync = async () => {
    setLoading(true);
    const toastId = toast.loading('Synchronizing AI Agents with Active Directory...');
    try {
      const response = await fetch('/api/v1/system/domain/sync', { method: 'POST' });
      if (response.ok) {
        const data = await response.json();
        setSyncStatus('success');
        setLastSync(new Date().toLocaleString());
        toast.success('Synchronization complete! Agents are now domain users.', { id: toastId });
      } else {
        throw new Error('Failed to synchronize with AD');
      }
    } catch (error) {
      setSyncStatus('error');
      toast.error(`Sync Error: ${error.message}`, { id: toastId });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col flex-1 gap-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <Shield className="text-cyan w-7 h-7" />
            Active Directory Integration
          </h2>
          <p className="text-gray-400 text-sm mt-1">Manage AI Agents as enterprise domain users in twisterlab.local</p>
        </div>
        
        <button
          onClick={triggerSync}
          disabled={loading}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-sm transition-all
            ${loading 
              ? 'bg-gray-800 text-gray-500 cursor-not-allowed' 
              : 'bg-cyan hover:bg-cyan-light text-black shadow-lg shadow-cyan/20 active:scale-95'}`}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Synchronizing...' : 'Sync Agents to AD'}
        </button>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <StatusCard 
          icon={<Users className="text-cyan" />} 
          label="Managed Identity" 
          value="twisterlab.local" 
          sub="Primary Domain"
        />
        <StatusCard 
          icon={<Database className="text-purple" />} 
          label="Target OU" 
          value="AI Agents" 
          sub="DC=twisterlab,DC=local"
        />
        <StatusCard 
          icon={<Shield className="text-emerald-500" />} 
          label="Auth Standard" 
          value="Kerberos / LDAP" 
          sub="Enterprise Grade"
        />
      </div>

      <div className="bg-panel border border-white/10 rounded-2xl overflow-hidden shadow-2xl flex-1 flex flex-col">
        <div className="px-6 py-4 border-b border-white/10 bg-white/5 flex justify-between items-center">
          <span className="text-xs font-black tracking-widest text-gray-400 uppercase">Synchronization History</span>
          {lastSync && (
            <span className="text-[10px] font-mono text-gray-500">Last Successful Sync: {lastSync}</span>
          )}
        </div>
        
        <div className="p-8 flex flex-col items-center justify-center flex-1 text-center">
          {!syncStatus ? (
            <>
              <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-6 border border-white/10">
                <RefreshCw className="w-10 h-10 text-gray-600" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Ready for Synchronization</h3>
              <p className="text-gray-400 max-w-md text-sm leading-relaxed">
                Trigger a sync to create or update AI Agent accounts in your local Active Directory. 
                This will allow agents to inherit enterprise permissions and policies.
              </p>
            </>
          ) : syncStatus === 'success' ? (
            <>
              <div className="w-20 h-20 rounded-full bg-emerald-500/10 flex items-center justify-center mb-6 border border-emerald-500/20 shadow-[0_0_30px_rgba(16,185,129,0.1)]">
                <CheckCircle className="w-10 h-10 text-emerald-500" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Fleet Synchronized</h3>
              <p className="text-gray-400 max-w-md text-sm leading-relaxed">
                All AI Agents are currently mapped to domain users. 
                New agents added to the registry will require a re-sync.
              </p>
            </>
          ) : (
            <>
              <div className="w-20 h-20 rounded-full bg-red-500/10 flex items-center justify-center mb-6 border border-red-500/20">
                <AlertTriangle className="w-10 h-10 text-red-500" />
              </div>
              <h3 className="text-lg font-bold text-white mb-2">Sync Failed</h3>
              <p className="text-gray-400 max-w-md text-sm leading-relaxed">
                Unable to communicate with the Domain Controller. Please verify that the TwisterLab Gateway has appropriate permissions and the AD module is installed.
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const StatusCard = ({ icon, label, value, sub }) => (
  <div className="bg-panel border border-white/10 rounded-2xl p-6 shadow-xl relative overflow-hidden group hover:border-white/20 transition-all">
    <div className="flex items-start justify-between">
      <div>
        <div className="text-[10px] font-black text-gray-500 uppercase tracking-widest mb-2">{label}</div>
        <div className="text-xl font-bold text-white mb-1">{value}</div>
        <div className="text-xs text-gray-500 font-mono">{sub}</div>
      </div>
      <div className="p-3 bg-white/5 rounded-xl border border-white/10 group-hover:scale-110 transition-transform">
        {React.cloneElement(icon, { size: 24 })}
      </div>
    </div>
  </div>
);

export default DomainSyncView;

import React, { useState, useEffect } from 'react';
import { Zap, ExternalLink, Workflow, Play, Settings, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

const AutomationsView = () => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/system/automations/workflows');
      if (response.ok) {
        const result = await response.json();
        // Handle n8n data structure which usually has a 'data' array
        const workflowsList = result.data || result;
        setWorkflows(workflowsList.map(wf => ({
          id: wf.id,
          name: wf.name,
          status: wf.active ? 'Active' : 'Paused',
          trigger: wf.trigger || 'Unknown',
          lastRun: wf.updatedAt ? new Date(wf.updatedAt).toLocaleTimeString() : 'Unknown'
        })));
      }
    } catch (error) {
      console.error("Failed to fetch n8n workflows", error);
      toast.error("Failed to sync with n8n studio");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  return (
    <div className="h-full flex flex-col gap-6 animate-fade-in relative z-10">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <Zap className="text-cyan w-7 h-7" />
            Automations Engine
          </h2>
          <p className="text-gray-400 text-sm mt-1">Manage n8n workflows and webhook integrations</p>
        </div>
        
        <div className="flex gap-3">
          <button 
            onClick={fetchWorkflows}
            className="p-2 bg-white/5 hover:bg-white/10 border border-white/10 text-gray-400 rounded-lg transition-all"
            title="Refresh List"
          >
            <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button 
            onClick={() => window.open('http://192.168.0.30:5678', '_blank')}
            className="flex items-center gap-2 bg-cyan/10 hover:bg-cyan/20 border border-cyan/30 text-cyan px-4 py-2 rounded-lg text-sm font-medium transition-all"
          >
            OPEN N8N STUDIO
            <ExternalLink className="w-4 h-4" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 overflow-y-auto pr-2 scrollbar-hide">
          {workflows.map((wf) => (
            <div key={wf.id} className="bg-gray-900/40 backdrop-blur-md border border-white/5 rounded-xl p-5 hover:border-cyan/30 transition-all flex items-center justify-between group">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-gray-800 rounded-lg border border-white/5 group-hover:bg-cyan/10 group-hover:border-cyan/20 transition-all">
                  <Workflow className="w-6 h-6 text-gray-400 group-hover:text-cyan" />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-100 text-lg">{wf.name}</h3>
                  <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                    <span className="flex items-center gap-1">
                      <span className={`w-2 h-2 rounded-full ${wf.status === 'Active' ? 'bg-green-500' : 'bg-yellow-500'}`}></span>
                      {wf.status}
                    </span>
                    <span>Trigger: {wf.trigger}</span>
                    <span>Last Run: {wf.lastRun}</span>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button className="p-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-all" title="Execute Now">
                  <Play className="w-4 h-4" />
                </button>
                <button className="p-2 bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-all" title="Settings">
                  <Settings className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
          {workflows.length === 0 && (
            <div className="text-center py-20 bg-gray-900/20 rounded-2xl border border-dashed border-white/5">
              <Workflow className="w-12 h-12 text-gray-700 mx-auto mb-4" />
              <p className="text-gray-500">No active workflows found in n8n studio.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default AutomationsView;

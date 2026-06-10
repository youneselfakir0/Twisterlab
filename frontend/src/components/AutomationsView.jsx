import React from 'react';
import { Zap, ExternalLink, Workflow, Play, Settings } from 'lucide-react';

const MOCK_WORKFLOWS = [
  { id: 1, name: 'TwisterLab - Infrastructure Monitoring Workflow', status: 'Active', trigger: 'Webhook', lastRun: '2 mins ago' },
  { id: 2, name: 'TwisterLab - Notion Sync', status: 'Active', trigger: 'Schedule', lastRun: '1 hour ago' },
  { id: 3, name: 'Daily Performance Report to Discord', status: 'Paused', trigger: 'Schedule', lastRun: '1 day ago' },
];

const AutomationsView = () => {
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
        
        <button 
          onClick={() => window.open('http://192.168.0.30:5678', '_blank')}
          className="flex items-center gap-2 bg-cyan/10 hover:bg-cyan/20 border border-cyan/30 text-cyan px-4 py-2 rounded-lg text-sm font-medium transition-all"
        >
          OPEN N8N STUDIO
          <ExternalLink className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 gap-4">
        {MOCK_WORKFLOWS.map((wf) => (
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
      </div>
    </div>
  );
};

export default AutomationsView;

import React, { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import { TelemetryProvider, useTelemetry } from './context/TelemetryContext';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import CommandCenter from './components/CommandCenter';
import MaestroAI from './components/MaestroAI';
import Settings from './components/Settings';
import KnowledgeBase from './components/KnowledgeBase';
import FleetRegistry from './components/FleetRegistry';
import AutomationsView from './components/AutomationsView';
import DomainSyncView from './components/DomainSyncView';
import { AlertTriangle } from 'lucide-react';

function AppContent() {
  const [currentView, setCurrentView] = useState('system');
  const { telemetry } = useTelemetry();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#020409] text-gray-100 font-sans relative">
      {/* Global Visual Effects */}
      <div className="scanline" />
      <div className="cyber-grid" />
      
      <Toaster position="top-right" toastOptions={{ 
        style: { background: '#080c18', color: '#fff', border: '1px solid rgba(0, 242, 255, 0.2)', backdropFilter: 'blur(10px)' },
        success: { iconTheme: { primary: '#00f2ff', secondary: '#080c18' } },
        error: { iconTheme: { primary: '#ef4444', secondary: '#080c18' } }
      }} />
      <Sidebar currentView={currentView} setCurrentView={setCurrentView} />
      <div className="flex flex-col flex-1 min-w-0 relative">
        <Topbar />
        
        {/* Critical Global System Alert Banner */}
        {!telemetry.config_ok && (
          <div className="mx-6 mt-4 bg-red-500/10 border border-red-500/30 p-4 rounded-xl flex items-center gap-4 animate-pulse shrink-0 relative z-50">
            <AlertTriangle className="text-red-500 animate-bounce" size={20} />
            <div className="flex-1">
              <div className="text-[11px] font-black text-red-500 uppercase tracking-widest">CRITICAL CONFIGURATION FAILURE</div>
              <div className="text-[10px] text-red-200/70 font-medium mt-0.5 uppercase tracking-tighter">Missing environment secrets detected. System orchestration may be compromised.</div>
            </div>
            <button className="px-4 py-1.5 bg-red-500 text-black text-[10px] font-black rounded-lg uppercase tracking-widest hover:bg-red-600 transition-colors">FIX NOW</button>
          </div>
        )}

        <main className="flex-1 overflow-y-auto p-6 flex flex-col relative z-10">
          {currentView === 'system' && <CommandCenter />}
          {currentView === 'ma' && <MaestroAI />}
          {currentView === 'st' && <Settings />}
          {currentView === 'no' && <KnowledgeBase />}
          {currentView === 'ag' && <FleetRegistry />}
          {currentView === 'n8' && <AutomationsView />}
          {currentView === 'ad' && <DomainSyncView />}
          
          {!['system', 'ma', 'st', 'no', 'ag', 'n8', 'ad'].includes(currentView) && (
            <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
              <div className="text-4xl mb-4 opacity-50">🚧</div>
              <div className="text-sm font-bold tracking-widest uppercase">Module In Development</div>
              <div className="text-xs mt-2 opacity-60">This section is being migrated to React Architecture.</div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function App() {
  return (
    <TelemetryProvider>
      <AppContent />
    </TelemetryProvider>
  );
}

export default App;

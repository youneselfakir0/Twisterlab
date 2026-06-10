import React, { useState } from 'react';
import { Toaster } from 'react-hot-toast';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import CommandCenter from './components/CommandCenter';
import MaestroAI from './components/MaestroAI';
import Settings from './components/Settings';
import KnowledgeBase from './components/KnowledgeBase';
import FleetRegistry from './components/FleetRegistry';
import AutomationsView from './components/AutomationsView';
import DomainSyncView from './components/DomainSyncView';

function App() {
  const [currentView, setCurrentView] = useState('system');

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-bg text-gray-100 font-sans">
      <Toaster position="top-right" toastOptions={{ 
        style: { background: '#1e293b', color: '#fff', border: '1px solid rgba(255,255,255,0.1)' },
        success: { iconTheme: { primary: '#10b981', secondary: '#1e293b' } },
        error: { iconTheme: { primary: '#ef4444', secondary: '#1e293b' } }
      }} />
      <Sidebar currentView={currentView} setCurrentView={setCurrentView} />
      <div className="flex flex-col flex-1 min-w-0 relative">
        <Topbar />
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

export default App;

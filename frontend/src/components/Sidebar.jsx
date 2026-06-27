import React from 'react';
import { 
  LayoutDashboard, Brain, Cpu, Shield, Zap, Book, Settings, Activity
} from 'lucide-react';

const Sidebar = ({ currentView, setCurrentView }) => {
  const navItems = [
    { id: 'system', icon: LayoutDashboard, label: 'Tactical Hub', section: 'COMMAND' },
    { id: 'ma', icon: Brain, label: 'Maestro Brain', section: 'COMMAND' },
    { id: 'ag', icon: Activity, label: 'Fleet Registry', section: 'COMMAND' },
    { id: 'ad', icon: Shield, label: 'Domain Sync', section: 'INTEL' },
    { id: 'n8', icon: Zap, label: 'Automations', section: 'INTEL' },
    { id: 'no', icon: Book, label: 'Knowledge', section: 'INTEL' },
    { id: 'st', icon: Settings, label: 'Core Config', section: 'SYSTEM' },
  ];

  return (
    <nav className="w-64 glass-panel border-r border-white/5 py-8 flex flex-col gap-8 shrink-0 relative z-20 shadow-[4px_0_24px_rgba(0,0,0,0.5)]">
      <div className="px-8 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-cyan/10 border border-cyan/30 flex items-center justify-center shadow-[0_0_15px_rgba(0,242,255,0.1)]">
            <div className="w-3.5 h-3.5 bg-cyan rounded-full animate-pulse shadow-[0_0_12px_#00f2ff]" />
          </div>
          <span className="font-black tracking-[0.25em] text-white text-xs italic">TWISTER<span className="text-cyan drop-shadow-[0_0_8px_rgba(0,242,255,0.4)]">LAB</span></span>
        </div>
      </div>

      <div className="flex flex-col gap-6 overflow-y-auto scrollbar-hide">
        {['COMMAND', 'INTEL', 'SYSTEM'].map(section => (
          <div key={section} className="flex flex-col gap-2">
            <div className="px-8 pb-1 text-[10px] font-black text-gray-600 uppercase tracking-[0.3em] opacity-80">{section}</div>
            <div className="flex flex-col gap-0.5">
              {navItems.filter(item => item.section === section).map(item => (
                <button
                  key={item.id}
                  onClick={() => setCurrentView(item.id)}
                  className={`flex items-center gap-4 px-8 py-3.5 text-[12px] font-bold transition-all relative text-left w-full group
                    ${currentView === item.id ? 'text-white' : 'text-gray-500 hover:text-gray-300 hover:bg-white/[0.02]'}`}
                >
                  {currentView === item.id && (
                    <>
                      <div className="absolute left-0 top-0 bottom-0 w-1 bg-cyan shadow-[0_0_20px_#00f2ff]" />
                      <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-cyan/5 to-transparent" />
                    </>
                  )}
                  <item.icon size={18} className={`transition-all duration-500 ${currentView === item.id ? 'text-cyan drop-shadow-[0_0_8px_rgba(0,242,255,0.6)] scale-110' : 'group-hover:text-white group-hover:scale-105'}`} />
                  <span className={`tracking-wide transition-all ${currentView === item.id ? 'translate-x-1' : ''}`}>{item.label}</span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="mt-auto px-8">
        <div className="p-5 rounded-2xl bg-black/60 border border-white/5 text-[10px] relative overflow-hidden group">
          <div className="absolute top-0 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-cyan/30 to-transparent" />
          <div className="flex justify-between items-center mb-2.5 relative z-10">
            <span className="text-gray-600 font-black uppercase tracking-[0.2em]">Security</span>
            <span className={`font-mono font-bold drop-shadow-[0_0_5px_currentColor] ${telemetry.config_ok ? 'text-cyan' : 'text-amber-500'}`}>
              {telemetry.config_ok ? 'ACTIVE' : 'DEGRADED'}
            </span>
          </div>
          <div className="h-1 bg-gray-900 rounded-full overflow-hidden relative z-10">
            <div className={`h-full bg-gradient-to-r transition-all duration-1000 ${telemetry.config_ok ? 'from-cyan/50 to-cyan shadow-[0_0_10px_#00f2ff] w-full' : 'from-amber-500/50 to-amber-500 shadow-[0_0_10px_#f59e0b] w-2/3'}`} />
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Sidebar;

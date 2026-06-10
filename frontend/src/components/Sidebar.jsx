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
    <nav className="w-64 glass-panel border-r border-white/5 py-8 flex flex-col gap-8 shrink-0 relative z-20">
      <div className="px-8 mb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-cyan/20 border border-cyan/40 flex items-center justify-center shadow-[0_0_15px_rgba(0,242,255,0.2)]">
            <div className="w-3 h-3 bg-cyan rounded-full animate-pulse shadow-[0_0_8px_#00f2ff]" />
          </div>
          <span className="font-black tracking-[0.2em] text-white text-xs">TWISTER<span className="text-cyan">LAB</span></span>
        </div>
      </div>

      {['COMMAND', 'INTEL', 'SYSTEM'].map(section => (
        <div key={section} className="flex flex-col gap-1">
          <div className="px-8 pb-2 text-[10px] font-black text-gray-500 uppercase tracking-[0.25em]">{section}</div>
          {navItems.filter(item => item.section === section).map(item => (
            <button
              key={item.id}
              onClick={() => setCurrentView(item.id)}
              className={`flex items-center gap-4 px-8 py-3 text-[12px] font-bold transition-all relative text-left w-full group
                ${currentView === item.id ? 'text-white' : 'text-gray-500 hover:text-gray-300 hover:bg-white/5'}`}
            >
              {currentView === item.id && (
                <>
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-cyan shadow-[0_0_15px_#00f2ff]" />
                  <div className="absolute right-0 top-0 bottom-0 w-24 bg-gradient-to-l from-cyan/5 to-transparent" />
                </>
              )}
              <item.icon size={18} className={`transition-all ${currentView === item.id ? 'text-cyan drop-shadow-[0_0_5px_rgba(0,242,255,0.5)]' : 'group-hover:text-white'}`} />
              <span className="tracking-wide">{item.label}</span>
            </button>
          ))}
        </div>
      ))}

      <div className="mt-auto px-8">
        <div className="p-4 rounded-lg bg-black/40 border border-white/5 text-[10px]">
          <div className="flex justify-between items-center mb-2">
            <span className="text-gray-500 font-bold uppercase tracking-wider">Security</span>
            <span className="text-cyan font-mono">ACTIVE</span>
          </div>
          <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
            <div className="h-full bg-cyan w-full shadow-[0_0_10px_#00f2ff]" />
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Sidebar;

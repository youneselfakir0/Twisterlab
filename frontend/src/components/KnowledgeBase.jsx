import React, { useState, useEffect } from 'react';
import { RefreshCw, FileText, Database, BookOpen, ExternalLink, HardDrive } from 'lucide-react';
import toast from 'react-hot-toast';

const MOCK_DOCS = [
  { id: 1, title: 'TwisterLab Architecture V4', type: 'Design Doc', date: '2 hrs ago', status: 'Synced', icon: Database },
  { id: 2, title: 'Maestro Agent Planning', type: 'Strategy', date: '5 hrs ago', status: 'Synced', icon: BookOpen },
  { id: 3, title: 'Agent Manifesto & Prompts', type: 'System', date: '1 day ago', status: 'Synced', icon: FileText },
  { id: 4, title: 'Infrastructure Audit Logs', type: 'Logs', date: '2 days ago', status: 'Archived', icon: HardDrive },
];

const KnowledgeBase = () => {
  const [isSyncing, setIsSyncing] = useState(false);
  const [documents, setDocuments] = useState([]);

  useEffect(() => {
    // Initial mock load
    setDocuments(MOCK_DOCS);
  }, []);

  const handleSync = async () => {
    setIsSyncing(true);
    toast.loading('Syncing Notion Workspace...', { id: 'notion-sync' });
    
    try {
      // Try to fetch from the actual TwisterLab API endpoint
      const response = await fetch('/api/dashboard/notion');
      if (response.ok) {
        const data = await response.json();
        if (data.pages && data.pages.length > 0) {
          const formattedDocs = data.pages.map((p, idx) => ({
            id: p.id || `live-${idx}`,
            title: p.title || 'Untitled',
            type: 'Notion Page',
            date: p.last_edited_time ? new Date(p.last_edited_time).toLocaleString() : 'Unknown',
            status: 'Synced',
            icon: FileText,
            url: p.url
          }));
          setDocuments(formattedDocs);
          toast.success('Workspace Synced Successfully', { id: 'notion-sync' });
          setIsSyncing(false);
          return;
        }
      }
    } catch (error) {
      console.log('Notion API fetch failed, falling back to mock data', error);
    }
    
    // Fallback to Mock Data if API fails (useful for local dev)
    setTimeout(() => {
      setIsSyncing(false);
      setDocuments([
        { id: 0, title: 'Maestro System Update', type: 'Report', date: 'Just now', status: 'Synced', icon: FileText },
        ...MOCK_DOCS
      ]);
      toast.success('Workspace Synced (Mock Mode)', { id: 'notion-sync' });
    }, 1500);
  };

  return (
    <div className="h-full flex flex-col gap-6 animate-fade-in relative z-10">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            <BookOpen className="text-cyan w-7 h-7" />
            Knowledge Base
          </h2>
          <p className="text-gray-400 text-sm mt-1">Notion Workspace Synchronization & Document Retrieval</p>
        </div>
        
        <button 
          onClick={handleSync}
          disabled={isSyncing}
          className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 border border-white/10 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin text-cyan' : 'text-gray-400'}`} />
          {isSyncing ? 'SYNCING...' : 'SYNC WORKSPACE'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {documents.map((doc) => {
          const Icon = doc.icon;
          return (
            <div 
              key={doc.id} 
              onClick={() => doc.url ? window.open(doc.url, '_blank') : null}
              className="bg-gray-900/40 backdrop-blur-md border border-white/5 rounded-xl p-5 hover:border-cyan/30 transition-all group cursor-pointer"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="p-2 bg-gray-800 rounded-lg border border-white/5 group-hover:bg-cyan/10 group-hover:border-cyan/20 transition-all">
                  <Icon className="w-5 h-5 text-gray-400 group-hover:text-cyan" />
                </div>
                <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-1 rounded-full ${doc.status === 'Synced' ? 'bg-green-500/10 text-green-400' : 'bg-gray-800 text-gray-400'}`}>
                  {doc.status}
                </span>
              </div>
              
              <h3 className="font-semibold text-gray-100 mb-1 group-hover:text-white line-clamp-2">
                {doc.title}
              </h3>
              
              <div className="flex items-center justify-between mt-4">
                <span className="text-xs text-gray-500 bg-gray-800 px-2 py-1 rounded-md">{doc.type}</span>
                <span className="text-xs text-gray-500">{doc.date}</span>
              </div>
              
              <div className="mt-4 pt-4 border-t border-white/5 flex items-center text-xs text-gray-400 hover:text-cyan transition-colors">
                <ExternalLink className="w-3 h-3 mr-1" />
                Open in Notion
              </div>
            </div>
          );
        })}
      </div>
      
      {documents.length === 0 && !isSyncing && (
        <div className="flex-1 flex flex-col items-center justify-center text-gray-500 bg-gray-900/20 rounded-xl border border-dashed border-white/10">
          <BookOpen className="w-12 h-12 mb-4 opacity-20" />
          <p>No documents found. Click Sync to fetch from Notion.</p>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBase;

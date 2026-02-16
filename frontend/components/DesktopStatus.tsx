'use client';

import React, { useEffect, useState } from 'react';
import { Terminal, Shield, CheckCircle, XCircle, Loader2, Database } from 'lucide-react';

const DesktopStatus = () => {
  const [status, setStatus] = useState<string>('checking');
  const [logs, setLogs] = useState<string[]>([]);
  const [isDesktop, setIsDesktop] = useState(false);

  useEffect(() => {
    const electronApi = typeof window !== 'undefined' ? window.electronAPI : undefined;
    const isElectron = !!electronApi;
    
    if (isElectron) {
      setTimeout(() => setIsDesktop(true), 0);
      
      const checkStatus = async () => {
        try {
          const s = await electronApi.getBackendStatus();
          setStatus(s);
        } catch {
          setStatus('error');
        }
      };

      checkStatus();
      const interval = setInterval(checkStatus, 5000);

      const logHandler = (log: string) => {
        setLogs((prev) => [...prev.slice(-4), log]);
      };

      const detachLogListener = electronApi.onBackendLog(logHandler);

      return () => {
        clearInterval(interval);
        detachLogListener?.();
      };
    }
  }, []);

  if (!isDesktop) return null;

  return (
    <div 
      className="fixed bottom-4 right-4 z-50 max-w-sm bg-slate-900/90 backdrop-blur border border-slate-700 rounded-lg p-4 shadow-2xl text-slate-200"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-indigo-400" />
          <h3 className="font-semibold text-sm">Desktop Engine</h3>
        </div>
        <div className="flex items-center gap-1">
          <Database className="w-3 h-3 text-slate-400" />
          <span className="text-[10px] text-slate-400 mr-2">DB: Active</span>
          {status === 'running' ? (
            <span className="flex items-center gap-1 text-xs text-emerald-400">
              <CheckCircle className="w-3 h-3" /> Online
            </span>
          ) : status === 'checking' ? (
            <span className="flex items-center gap-1 text-xs text-amber-400">
              <Loader2 className="w-3 h-3 animate-spin" /> Starting
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs text-rose-400">
              <XCircle className="w-3 h-3" /> Offline
            </span>
          )}
        </div>
      </div>

      <div className="bg-slate-950 rounded p-2 text-[10px] font-mono h-24 overflow-hidden border border-slate-800">
        <div className="flex items-center gap-1 border-b border-slate-800 mb-1 pb-1 text-slate-500">
          <Terminal className="w-3 h-3" />
          <span>System Output</span>
        </div>
        {logs.length > 0 ? (
          logs.map((log, i) => (
            <div key={i} className="whitespace-pre-wrap break-all opacity-80 mb-1">
              {log}
            </div>
          ))
        ) : (
          <div className="text-slate-600 italic">Waiting for initialization...</div>
        )}
      </div>
    </div>
  );
};

export default DesktopStatus;

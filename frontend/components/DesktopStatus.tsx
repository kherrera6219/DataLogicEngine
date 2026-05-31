'use client';

import React, { useEffect, useState } from 'react';
import { Terminal, Shield, CheckCircle, XCircle, Loader2, Database, Users, Wifi, Cpu, Minus } from 'lucide-react';
import { getLocalStorageItem, setLocalStorageItem } from '@/lib/state/storage';

const COLLAPSE_STORAGE_KEY = 'desktopEngine.collapsed';

interface DSQPPersonaProfile {
  axis: number;
  persona_type: string;
  name: string;
  coverage_score: number;
  job_role: string;
  skills: string[];
  chain_steps: number;
}

const DesktopStatus = () => {
  const [status, setStatus] = useState<string>('checking');
  const [logs, setLogs] = useState<string[]>([]);
  const [isDesktop, setIsDesktop] = useState(false);
  const [dsqpProfiles, setDsqpProfiles] = useState<DSQPPersonaProfile[]>([]);
  const [networkState, setNetworkState] = useState<string>('checking');
  const [localModel, setLocalModel] = useState<string | null>(null);
  // Restore the user's minimize preference (read during initial client render so
  // the panel never blocks the screen on load).
  const [collapsed, setCollapsed] = useState(() => {
    if (typeof window !== 'undefined') {
      return getLocalStorageItem(COLLAPSE_STORAGE_KEY) === '1';
    }
    return false;
  });

  const updateCollapsed = (next: boolean) => {
    setCollapsed(next);
    setLocalStorageItem(COLLAPSE_STORAGE_KEY, next ? '1' : '0');
  };

  useEffect(() => {
    const electronApi = typeof window !== 'undefined' ? window.electronAPI : undefined;
    const isElectron = !!electronApi;
    
    if (isElectron) {
      setTimeout(() => setIsDesktop(true), 0);
      
      const checkStatus = async () => {
        try {
          const s = await electronApi.getBackendStatus();
          setStatus(s);
          if (s === 'running' && electronApi.dsqpPersonaProfiles) {
            const dsqp = await electronApi.dsqpPersonaProfiles();
            setDsqpProfiles(Array.isArray(dsqp.profiles) ? dsqp.profiles.slice(0, 4) : []);
          }
          if (s === 'running' && electronApi.getNetworkStatus) {
            const network = await electronApi.getNetworkStatus();
            setNetworkState(network.state);
          }
          if (s === 'running' && electronApi.getLocalModelStatus) {
            const model = await electronApi.getLocalModelStatus();
            setLocalModel(model.active_model);
          }
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

  const statusDotClass =
    status === 'running' ? 'bg-emerald-400' : status === 'checking' ? 'bg-amber-400' : 'bg-rose-400';

  // Collapsed: a small pill in the corner so it never blocks the screen.
  if (collapsed) {
    return (
      <button
        type="button"
        onClick={() => updateCollapsed(false)}
        className="fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-full border border-slate-700 bg-slate-900/90 px-3 py-2 text-slate-200 shadow-2xl backdrop-blur transition-colors hover:bg-slate-800"
        title="Show Desktop Engine status"
        aria-label="Show Desktop Engine status"
      >
        <Shield className="h-4 w-4 text-indigo-400" />
        <span className={`h-2 w-2 rounded-full ${statusDotClass}`} />
      </button>
    );
  }

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
          <button
            type="button"
            onClick={() => updateCollapsed(true)}
            className="ml-1 rounded p-0.5 text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-200"
            title="Minimize Desktop Engine panel"
            aria-label="Minimize Desktop Engine panel"
          >
            <Minus className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>

      <div className="mb-3 grid grid-cols-2 gap-2 text-[10px]">
        <div className="flex min-w-0 items-center gap-1 rounded border border-slate-800 bg-slate-950/80 px-2 py-1 text-slate-300">
          <Wifi className="h-3 w-3 shrink-0 text-slate-500" />
          <span className="truncate">{networkState}</span>
        </div>
        <div className="flex min-w-0 items-center gap-1 rounded border border-slate-800 bg-slate-950/80 px-2 py-1 text-slate-300">
          <Cpu className="h-3 w-3 shrink-0 text-slate-500" />
          <span className="truncate">{localModel || 'No local model'}</span>
        </div>
      </div>

      {dsqpProfiles.length > 0 && (
        <div className="mb-3 rounded border border-slate-800 bg-slate-950/80 p-2">
          <div className="mb-2 flex items-center gap-1 text-[10px] font-medium text-slate-400">
            <Users className="h-3 w-3" />
            <span>DSQP Personas</span>
          </div>
          <div className="grid grid-cols-2 gap-1.5">
            {dsqpProfiles.map((profile) => (
              <div key={profile.axis} className="min-w-0 rounded border border-slate-800 bg-slate-900 px-2 py-1">
                <div className="truncate text-[10px] font-semibold text-slate-200">
                  A{profile.axis} {profile.persona_type}
                </div>
                <div className="truncate text-[9px] text-slate-500">
                  {profile.chain_steps}/7 steps · {Math.round(profile.coverage_score * 100)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

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

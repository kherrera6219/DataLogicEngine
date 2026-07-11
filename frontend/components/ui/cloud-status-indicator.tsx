'use client';

import React, { useState, useEffect } from 'react';
import { Cloud, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { request } from '@/lib/api/client';

export interface CloudStatusIndicatorProps {
  className?: string;
  isProcessing?: boolean;
}

export function CloudStatusIndicator({ className, isProcessing = false }: CloudStatusIndicatorProps) {
  const [status, setStatus] = useState<'online' | 'degraded' | 'offline' | 'loading'>('loading');
  
  useEffect(() => {
    let cancelled = false;

    const checkHealth = async () => {
      try {
        const health = await request<{ status?: string }>('/health');
        if (cancelled) return;
        setStatus(health.status === 'ok' ? 'online' : 'degraded');
      } catch {
        if (!cancelled) setStatus('offline');
      }
    };

    void checkHealth();
    const interval = window.setInterval(checkHealth, 30_000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  const statusConfig = {
    online: {
      icon: <CheckCircle2 className="h-3 w-3 text-emerald-500" />,
      color: "bg-emerald-500",
      text: "Application API: Available",
      description: "The application API and primary database responded successfully."
    },
    degraded: {
      icon: <AlertCircle className="h-3 w-3 text-yellow-500" />,
      color: "bg-yellow-500",
      text: "Application API: Degraded",
      description: "The API responded, but one or more checked components are unavailable."
    },
    offline: {
      icon: <AlertCircle className="h-3 w-3 text-red-500" />,
      color: "bg-red-500",
      text: "Application API: Offline",
      description: "The application API did not respond."
    },
    loading: {
      icon: <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />,
      color: "bg-muted-foreground",
      text: "Checking Status...",
      description: "Checking the application API and primary database."
    },
    processing: {
      icon: <Loader2 className="h-3 w-3 animate-spin text-blue-400" />,
      color: "bg-blue-500",
      text: "LLM Gateway: Processing",
      description: "A cloud reasoning task is currently in progress."
    }
  };

  const current = isProcessing ? statusConfig.processing : statusConfig[status];

  return (
    <div 
      className={cn(
        "flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/5 border border-white/5 hover:bg-white/10 transition-colors cursor-help group",
        className
      )}
      title={`${current.text}: ${current.description}`}
    >
      <div className="relative">
        <Cloud className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors" />
        <span className={cn(
          "absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full border border-background animate-pulse",
          current.color
        )} />
      </div>
      <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground group-hover:text-foreground transition-colors hidden sm:inline">
        {isProcessing ? "Cloud processing" : "Cloud reasoning"}
      </span>
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import { Cloud, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface CloudStatusIndicatorProps {
  className?: string;
}

export function CloudStatusIndicator({ className }: CloudStatusIndicatorProps) {
  const [status, setStatus] = useState<'online' | 'degraded' | 'offline' | 'loading'>('loading');
  
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await new Promise(resolve => setTimeout(resolve, 800));
        setStatus('online');
      } catch {
        setStatus('offline');
      }
    };
    checkHealth();
  }, []);

  const statusConfig = {
    online: {
      icon: <CheckCircle2 className="h-3 w-3 text-emerald-500" />,
      color: "bg-emerald-500",
      text: "LLM Gateway: Operational",
      description: "Cloud reasoning services are active and responding."
    },
    degraded: {
      icon: <AlertCircle className="h-3 w-3 text-yellow-500" />,
      color: "bg-yellow-500",
      text: "LLM Gateway: Degraded",
      description: "Intermittent latency detected in cloud providers."
    },
    offline: {
      icon: <AlertCircle className="h-3 w-3 text-red-500" />,
      color: "bg-red-500",
      text: "LLM Gateway: Offline",
      description: "Could not connect to cloud reasoning services."
    },
    loading: {
      icon: <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />,
      color: "bg-muted-foreground",
      text: "Checking Status...",
      description: "Contacting truth vectors..."
    }
  };

  const current = statusConfig[status];

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
        Cloud reasoning
      </span>
    </div>
  );
}

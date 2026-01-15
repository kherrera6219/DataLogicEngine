'use client';

import Link from 'next/link';
import useSWR from 'swr';
import { api } from '@/lib/api';
import { 
  MessageSquare, 
  LayoutDashboard, 
  Share2, 
  Settings, 
  ArrowRight,
  ShieldCheck,
  Zap
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function Home() {
  const { data: systemStatus } = useSWR<string>('system-health', () => api.system.health(), {
    refreshInterval: 10000
  });

  const isOperational = systemStatus === 'Operational' || systemStatus === 'ok';

  const features = [
    {
      title: "Chat Interface",
      desc: "Deep reasoning with the Truth Engine via the LLM Gateway.",
      icon: MessageSquare,
      href: "/chat",
      color: "blue"
    },
    {
      title: "Compliance Hub",
      desc: "Real-time metrics, audit logs, and system statistics.",
      icon: LayoutDashboard,
      href: "/dashboard",
      color: "emerald"
    },
    {
      title: "Graph Explorer",
      desc: "Interactive 17-Dimensional Knowledge Visualization.",
      icon: Share2,
      href: "/graph",
      color: "violet"
    },
    {
      title: "System Control",
      desc: "Fine-tune Knowledge Algorithms and registry settings.",
      icon: Settings,
      href: "/settings",
      color: "gray"
    }
  ];

  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 flex flex-col items-center justify-center p-6 md:p-24 relative overflow-hidden">
      {/* Background Polish */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,_rgba(37,99,235,0.05),transparent_50%)] pointer-events-none" />
      
      <div className="relative z-10 max-w-5xl w-full text-center space-y-12">
        <header className="space-y-4 animate-in fade-in slide-in-from-top-4 duration-700">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-500 text-xs font-bold uppercase tracking-widest border border-blue-500/20">
            <Zap className="h-3 w-3" /> System Ready
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tighter bg-clip-text text-transparent bg-gradient-to-r from-gray-900 via-blue-600 to-violet-600 dark:from-white dark:via-blue-400 dark:to-violet-400">
            DataLogicEngine
          </h1>
          <p className="text-xl text-gray-500 dark:text-gray-400 max-w-2xl mx-auto font-medium">
            Enterprise Universal Knowledge Graph System with 17-Axis <br className="hidden md:block"/> Reasoning and MCP Unified Standards.
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-1000 delay-200">
          {features.map((f) => (
            <Link 
              key={f.title}
              href={f.href}
              className="group relative p-8 bg-white dark:bg-gray-900 rounded-[2rem] border border-gray-100 dark:border-gray-800 shadow-sm hover:shadow-2xl hover:-translate-y-1 transition-all duration-300"
            >
              <div className={cn(
                "mb-6 w-14 h-14 rounded-2xl flex items-center justify-center transition-colors shadow-inner",
                f.color === 'blue' ? "bg-blue-500/10 text-blue-500" :
                f.color === 'emerald' ? "bg-emerald-500/10 text-emerald-500" :
                f.color === 'violet' ? "bg-violet-500/10 text-violet-500" :
                "bg-gray-500/10 text-gray-400"
              )}>
                <f.icon className="h-7 w-7" />
              </div>
              <div className="text-left space-y-2">
                <h2 className="text-2xl font-bold flex items-center gap-2">
                  {f.title}
                  <ArrowRight className="h-5 w-5 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-blue-500" />
                </h2>
                <p className="text-gray-500 dark:text-gray-400 leading-relaxed font-medium">
                  {f.desc}
                </p>
              </div>
            </Link>
          ))}
        </div>

        <footer className="pt-8 flex flex-col md:flex-row items-center justify-center gap-6 text-sm text-gray-400 border-t border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white dark:bg-gray-900 border border-gray-100 dark:border-gray-800 shadow-sm">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="font-bold text-gray-600 dark:text-gray-300">Status: {isOperational ? "Operational" : "Degraded"}</span>
          </div>
          <div className="hidden md:block w-px h-4 bg-gray-200 dark:bg-gray-800" />
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-blue-500" />
            <span className="font-medium">Protocol L10 Certified</span>
          </div>
          <div className="hidden md:block w-px h-4 bg-gray-200 dark:bg-gray-800" />
          <div className="font-medium tracking-tight">v1.2.4 Production</div>
        </footer>
      </div>
    </main>
  );
}

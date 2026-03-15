'use client';

import Link from 'next/link';
import useSWR from 'swr';
import { api } from '@/lib/api';
import { 
  MessageSquare, 
  LayoutDashboard, 
  Share2, 
  Settings, 
  ShieldCheck,
  Zap,
  ArrowRight
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Badge } from "@/components/ui/badge";

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
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      border: "border-blue-500/20"
    },
    {
      title: "Compliance Hub",
      desc: "Real-time metrics, audit logs, and system statistics.",
      icon: LayoutDashboard,
      href: "/dashboard",
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/20"
    },
    {
      title: "Graph Explorer",
      desc: "Interactive 17-Dimensional Knowledge Visualization.",
      icon: Share2,
      href: "/graph",
      color: "text-violet-400",
      bg: "bg-violet-500/10",
      border: "border-violet-500/20"
    },
    {
      title: "System Control",
      desc: "Fine-tune Knowledge Algorithms and registry settings.",
      icon: Settings,
      href: "/settings",
      color: "text-gray-400",
      bg: "bg-gray-500/10",
      border: "border-gray-500/20"
    },
    {
       title: "Data Sovereignty",
       desc: "Protected by KA-61 Adversarial Shields & Zero Retention policies.",
       icon: ShieldCheck,
       href: "/about/cloud-services",
       color: "text-blue-400",
       bg: "bg-blue-500/10",
       border: "border-blue-500/20"
    },
    {
       title: "Knowledge Base",
       desc: "Browse nodes, edges, and relationships in the knowledge graph.",
       icon: Share2,
       href: "/knowledge",
       color: "text-violet-400",
       bg: "bg-violet-500/10",
       border: "border-violet-500/20"
    }
  ];

  return (
    <main className="min-h-screen bg-gray-100 dark:bg-[#0a0a0a] text-gray-900 dark:text-white flex flex-col items-center justify-center p-6 md:p-24 relative overflow-hidden bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">
      {/* Background Polish */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-gray-100/80 to-gray-100 dark:via-[#0a0a0a]/80 dark:to-[#0a0a0a] pointer-events-none" />
      
      <div className="relative z-10 max-w-5xl w-full text-center space-y-12 animate-in fade-in zoom-in-95 duration-1000">
        <header className="space-y-6">
          <Badge variant="outline" className={cn(
            "px-4 py-1.5 text-xs font-bold uppercase tracking-widest backdrop-blur-md",
            isOperational 
              ? "bg-blue-500/10 text-blue-400 border-blue-500/20" 
              : "bg-red-500/10 text-red-400 border-red-500/20"
          )}>
            <Zap className="h-3 w-3 mr-2 fill-blue-500/20" /> {isOperational ? 'System Operational' : 'System Degraded'}
          </Badge>
          
          <div className="space-y-4">
             <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-gray-900 dark:text-white drop-shadow-2xl">
               DataLogic<span className="text-blue-500">Engine</span>
             </h1>
             <p className="text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto font-light leading-relaxed">
               Enterprise Universal Knowledge Graph System with 17-Axis Reasoning and MCP Unified Standards.
             </p>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <Link 
              key={f.title}
              href={f.href}
              className="group relative"
            >
              <div className="h-full p-8 bg-white/90 dark:bg-[#151515] hover:bg-white dark:hover:bg-[#1a1a1a] rounded-2xl border border-slate-300/70 dark:border-white/5 hover:border-slate-400/70 dark:hover:border-white/10 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 group hover:ring-1 hover:ring-blue-500/30">
                <div className={cn(
                  "mb-6 w-14 h-14 rounded-xl flex items-center justify-center transition-all shadow-inner border border-white/5",
                  f.bg, f.color
                )}>
                  <f.icon className="h-7 w-7" />
                </div>
                
                <h3 className="text-xl font-bold mb-3 text-slate-900 dark:text-gray-100 group-hover:text-slate-950 dark:group-hover:text-white transition-colors flex items-center gap-2">
                  {f.title}
                  <ArrowRight className="h-4 w-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-blue-500" />
                </h3>
                
                <p className="text-sm text-slate-600 dark:text-gray-400 leading-relaxed group-hover:text-slate-800 dark:group-hover:text-gray-300 transition-colors">
                  {f.desc}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}

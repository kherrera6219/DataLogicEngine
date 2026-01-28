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
import { Button } from "@/components/ui/button";
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
       desc: "Explore the 17-dimensional graph visualization engine.",
       icon: Share2,
       href: "/graph",
       color: "text-violet-400",
       bg: "bg-violet-500/10",
       border: "border-violet-500/20"
    }
  ];

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white flex flex-col items-center justify-center p-6 md:p-24 relative overflow-hidden bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">
      {/* Background Polish */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0a0a0a]/80 to-[#0a0a0a] pointer-events-none" />
      
      <div className="relative z-10 max-w-5xl w-full text-center space-y-12 animate-in fade-in zoom-in-95 duration-1000">
        <header className="space-y-6">
          <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20 px-4 py-1.5 text-xs font-bold uppercase tracking-widest backdrop-blur-md">
            <Zap className="h-3 w-3 mr-2 fill-blue-500/20" /> System Operational
          </Badge>
          
          <div className="space-y-4">
             <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-white drop-shadow-2xl">
               DataLogic<span className="text-blue-500">Engine</span>
             </h1>
             <p className="text-xl text-gray-400 max-w-2xl mx-auto font-light leading-relaxed">
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
              <div className="h-full p-8 bg-[#151515] hover:bg-[#1a1a1a] rounded-2xl border border-white/5 hover:border-white/10 shadow-lg hover:shadow-2xl transition-all duration-300 hover:-translate-y-1 group hover:ring-1 hover:ring-blue-500/30">
                <div className={cn(
                  "mb-6 w-14 h-14 rounded-xl flex items-center justify-center transition-all shadow-inner border border-white/5",
                  f.bg, f.color
                )}>
                  <f.icon className="h-7 w-7" />
                </div>
                
                <h3 className="text-xl font-bold mb-3 text-gray-100 group-hover:text-white transition-colors flex items-center gap-2">
                  {f.title}
                  <ArrowRight className="h-4 w-4 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all text-blue-500" />
                </h3>
                
                <p className="text-sm text-gray-400 leading-relaxed group-hover:text-gray-300 transition-colors">
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
footer className="pt-8 flex flex-col md:flex-row items-center justify-center gap-6 text-sm text-gray-400 border-t border-gray-100 dark:border-gray-800">
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
          <div className="hidden md:block w-px h-4 bg-gray-200 dark:bg-gray-800" />
           <div className="flex gap-4">
             <Link href="/legal/privacy" className="hover:text-blue-500 transition-colors">Privacy</Link>
             <Link href="/about" className="hover:text-blue-500 transition-colors">About</Link>
           </div>
        </footer>
      </div>
    </main>
  );
}

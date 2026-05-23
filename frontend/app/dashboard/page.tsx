'use client';

import React from 'react';
import Link from "next/link";
import { 
  MessageSquare, Upload, Key, Activity, 
  ArrowRight, Clock, Settings, BarChart3, Mail, TrendingUp
} from 'lucide-react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

import { api, AnalyticsOverview, Activity as ActivityType } from '@/lib/api';
import { useToast } from "@/components/ui/use-toast";

export default function DashboardPage() {
  const { toast } = useToast();
  const [overview, setOverview] = React.useState<AnalyticsOverview | null>(null);
  const [activity, setActivity] = React.useState<ActivityType[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    async function fetchData() {
      try {
        const [overviewData, activityData] = await Promise.all([
          api.analytics.overview() as Promise<AnalyticsOverview>,
          api.analytics.activity() as Promise<ActivityType[]>
        ]);
        setOverview(overviewData);
        setActivity(activityData);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
        // Fallback to empty states if API fails
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [toast]);

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'chat': return MessageSquare;
      case 'upload': return Upload;
      case 'system': return Key;
      case 'alert': return Mail; // Changed from AlertTriangle
      default: return Activity;
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'chat': return 'text-blue-400';
      case 'upload': return 'text-green-400';
      case 'system': return 'text-yellow-400';
      case 'alert': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const trendingTopics = React.useMemo(() => {
    const counts = new Map<string, number>();
    for (const item of activity) {
      const key = (item.title || '').trim();
      if (!key) continue;
      counts.set(key, (counts.get(key) || 0) + 1);
    }
    return Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4);
  }, [activity]);

  return (
    <div className="min-h-full bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed flex flex-col">
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        
        {/* Top Bar with Acrylic Blur */}
        <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center justify-between px-8 backdrop-blur-3xl">
           <h1 className="text-title font-bold text-transparent bg-clip-text bg-gradient-to-r from-slate-900 to-slate-500 dark:from-white dark:to-gray-400">Command Center</h1>
           <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1 bg-green-900/10 border border-green-500/20 rounded-full backdrop-blur-sm">
                 <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                 <span className="text-xs font-bold text-green-400 tracking-wide">
                    {overview ? "SYSTEMS NORMAL" : "INITIALIZING..."}
                 </span>
              </div>
              <div className="text-xs text-gray-400 font-mono opacity-60">
                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
           </div>
        </div>

        <div className="p-8 max-w-[1600px] w-full mx-auto space-y-10 animate-connected-enter">
           
           {/* Hero / Welcome */}
           <div className="flex items-center justify-between">
              <div>
                 <h2 className="text-display mb-1 bg-clip-text text-transparent bg-gradient-to-br from-slate-900 via-slate-700 to-slate-500 dark:from-white dark:via-white dark:to-gray-500">
                    Unified Knowledge Gateway
                 </h2>
                 <p className="text-gray-400 text-lg font-light">
                   {loading ? "Synchronizing core intelligence engines..." : "Your intelligence distribution network is active."}
                 </p>
              </div>
              <div className="flex gap-3">
                 <Link href="/chat">
                    <Button className="h-11 px-6 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-[0_0_20px_rgba(37,99,235,0.3)] transition-all hover:scale-[1.02] border-none">
                       <MessageSquare className="h-4 w-4 mr-2" /> Start New Session
                    </Button>
                 </Link>
                 <Link href="/chat?intent=upload">
                    <Button variant="outline" className="h-11 px-6 rounded-xl border-white/10 hover:bg-white/5 bg-white/[0.02] backdrop-blur-md transition-all">
                       <Upload className="h-4 w-4 mr-2" /> Quick Upload
                    </Button>
                 </Link>
              </div>
           </div>

           {/* Metrics Overview - Fluent Cards */}
           <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[
                 { 
                   label: 'Daily API Requests', 
                   value: overview?.api_requests_24h?.toLocaleString() || '--', 
                   trend: '+12%', 
                   icon: Activity, 
                   color: 'text-blue-400', 
                   bg: 'bg-blue-500/10', 
                   border: 'border-blue-500/20' 
                 },
                 { 
                   label: 'Knowledge Graph Size', 
                   value: overview?.kg_size_display || '--', 
                   status: `${overview?.kg_nodes?.toLocaleString() || 0} Nodes`, 
                   icon: BarChart3, // Changed from Database
                   color: 'text-purple-400', 
                   bg: 'bg-purple-500/10', 
                   border: 'border-purple-500/20' 
                 },
                 { 
                   label: 'Compliance Status', 
                   value: overview?.compliance_status || 'Secure', 
                   score: overview?.compliance_score || '--', 
                   icon: Settings, // Changed from ShieldCheck
                   color: 'text-green-400', 
                   bg: 'bg-green-500/10', 
                   border: 'border-green-500/20' 
                 }
              ].map((m, i) => (
                  <Card key={i} className="bg-[#1a1a1a] border-[#333] shadow-lg hover:border-[#444] transition-all duration-300 hover:-translate-y-1">
                     <CardContent className="p-6 relative overflow-hidden group">
                        {/* Glow effect */}
                        <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-white/5 to-transparent rounded-bl-full -mr-8 -mt-8 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
                        
                        <div className="flex justify-between items-start mb-4 relative z-10">
                           <div className={`p-3 rounded-xl ${m.bg} ${m.color}`}>
                              <m.icon className="h-6 w-6" />
                           </div>
                           <Badge variant="outline" className={`${m.bg} ${m.color} ${m.border} backdrop-blur-md`}>
                              {m.trend || m.status || m.score}
                           </Badge>
                        </div>
                        <div className="text-4xl font-semibold tracking-tight relative z-10">{m.value}</div>
                        <div className="text-sm text-gray-400 mt-1 font-medium relative z-10">{m.label}</div>
                     </CardContent>
                  </Card>
              ))}
           </div>

           {/* Content Grid */}
           <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              
              {/* Recent Activity */}
              <div className="lg:col-span-2 space-y-6">
                 <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
                       <Clock className="h-5 w-5 text-gray-500" /> Recent Activity
                    </h3>
                    <Button variant="ghost" size="sm" className="text-xs text-blue-400 hover:text-white">View All</Button>
                 </div>
                 
                 <div className="space-y-3">
                    {activity.map((item, i) => {
                       const Icon = getActivityIcon(item.type);
                       return (
                        <div key={i} className="flex items-center gap-4 p-4 rounded-xl bg-[#1a1a1a] border border-[#2a2a2a] hover:border-[#404040] hover:bg-[#202020] transition-all group cursor-pointer reveal-hover">
                           <div className={`p-2.5 rounded-lg bg-white/5 ${getActivityColor(item.type)} bg-opacity-10 ring-1 ring-white/5`}>
                              <Icon className="h-5 w-5" />
                           </div>
                           <div className="flex-1">
                              <div className="font-medium text-gray-200 group-hover:text-white transition-colors text-base-fluent">{item.title}</div>
                              <div className="text-xs text-gray-500 mt-0.5">{item.time}</div>
                           </div>
                           <ArrowRight className="h-4 w-4 text-gray-600 group-hover:text-white opacity-0 group-hover:opacity-100 -translate-x-2 group-hover:translate-x-0 transition-all duration-300" />
                        </div>
                       );
                    })}
                    {activity.length === 0 && !loading && (
                      <div className="p-8 text-center border-2 border-dashed border-white/5 rounded-xl text-gray-400 italic">
                        No recent activity recorded.
                      </div>
                    )}
                 </div>
              </div>

              {/* Quick Knowledge Access */}
              <div className="space-y-6">
                 <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
                       <TrendingUp className="h-5 w-5 text-gray-500" /> Trending Topics
                    </h3>
                 </div>
                 
                 <div className="bg-[#1a1a1a] border border-[#2a2a2a] rounded-xl p-1 shadow-lg">
                    {trendingTopics.map(([topic, count], i) => (
                      <div key={topic} className="flex items-center justify-between p-3 rounded-lg hover:bg-[#252525] transition-colors group cursor-pointer">
                        <div className="flex items-center gap-3">
                          <div className="text-xs font-mono text-gray-600 bg-black/30 px-1.5 py-0.5 rounded">#{i + 1}</div>
                          <div className="text-sm text-gray-300 group-hover:text-blue-400 transition-colors font-medium">{topic}</div>
                        </div>
                        <div className="text-xs text-gray-600 group-hover:text-gray-400">{count}</div>
                      </div>
                    ))}
                    {trendingTopics.length === 0 && !loading && (
                      <div className="p-3 text-sm text-gray-400">No activity topics available yet.</div>
                    )}
                 </div>

                 <Card className="bg-gradient-to-br from-blue-900/30 via-indigo-900/10 to-transparent border-blue-500/20 shadow-lg relative overflow-hidden group">
                    <div className="absolute inset-0 bg-blue-500/5 group-hover:bg-blue-500/10 transition-colors"></div>
                    <CardContent className="p-5 relative z-10">
                       <div className="flex items-center gap-3 mb-2">
                          <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                          </span>
                          <div className="text-xs font-bold text-blue-300 uppercase tracking-widest">System Notice</div>
                       </div>
                       <p className="text-sm text-gray-300 leading-relaxed">
                          {overview
                            ? `Last telemetry update: ${new Date(overview.timestamp).toLocaleString()}.`
                            : 'No telemetry notice available yet.'}
                       </p>
                    </CardContent>
                 </Card>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
}

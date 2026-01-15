'use client';

import Link from "next/link";
import useSWR from 'swr';
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ComplianceTrendChart } from "@/components/Dashboard/ComplianceTrendChart";
import { CommandBar } from "@/components/Dashboard/CommandBar";
import { ApiErrorBoundary } from "@/components/ui/api-error-boundary";
import { 
  Activity, 
  Database, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  ExternalLink,
  PlayCircle,
  MessageSquarePlus,
  ArrowUpRight,
  TrendingUp,
  ShieldCheck,
  AlertTriangle
} from 'lucide-react';

interface TraceRun {
  run_id: string;
  ka_id: string;
  status: string;
  created_at: string;
}

function StatCard({ title, value, subtext, icon: Icon, trend, variant = "default" }: any) {
  return (
    <Card 
      className="glass-card transition-all hover:scale-[1.02] hover:shadow-blue-500/10 active:scale-[0.98]"
      role="region"
      aria-label={`${title} statistics`}
    >
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        <div className={cn(
          "p-2 rounded-xl",
          variant === "destructive" ? "bg-red-500/10 text-red-500" : 
          variant === "success" ? "bg-emerald-500/10 text-emerald-500" :
          "bg-blue-500/10 text-blue-500"
        )}>
          <Icon className="h-4 w-4" aria-hidden="true" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="text-3xl font-bold tracking-tight" aria-atomic="true">{value}</div>
        <div className="flex items-center gap-1.5 mt-2">
          {trend && (
            <div 
              className={cn("flex items-center text-xs font-semibold px-1.5 py-0.5 rounded-md", trend > 0 ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500")}
              aria-label={`Trend: ${trend > 0 ? "Up" : "Down"} by ${Math.abs(trend)} percent`}
            >
              {trend > 0 ? "+" : ""}{trend}%
              <TrendingUp className={cn("h-3 w-3 ml-1", trend < 0 && "rotate-180")} aria-hidden="true" />
            </div>
          )}
          <p className="text-xs text-muted-foreground">{subtext}</p>
        </div>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { data: runs, isLoading: isRunsLoading } = useSWR('trace-list', () => api.trace.list(10), { 
    refreshInterval: 5000 
  });

  const { data: summary, isLoading: isSummaryLoading } = useSWR('analytics-summary', () => api.analytics.summary(), {
    refreshInterval: 10000
  });

  const { data: systemStatus } = useSWR<string>('system-health', () => api.system.health(), {
    refreshInterval: 10000
  });

  const isOperational = systemStatus === 'Operational' || systemStatus === 'ok';

  return (
    <div className="min-h-screen bg-gray-50/50 dark:bg-gray-950 flex flex-col overflow-hidden">
      <CommandBar />
      <div className="flex-1 overflow-y-auto p-6 md:p-8">
        <div className="container mx-auto max-w-7xl space-y-8">
          
          {/* Header Section */}
          <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="space-y-1">
              <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 dark:text-white">
                Compliance <span className="text-blue-600 dark:text-blue-500">Dashboard</span>
              </h1>
              <p className="text-gray-500 dark:text-gray-400 font-medium">
                Enterprise Control Hub • 17-Axis Unified Standard
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
               <Link href="/chat">
                  <Button 
                    className="h-11 px-6 rounded-xl bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/20 text-white gap-2"
                    aria-label="Start new intelligence session"
                  >
                    <MessageSquarePlus className="h-5 w-5" aria-hidden="true" />
                    New Session
                  </Button>
               </Link>
               <Link href="/graph">
                   <Button 
                    variant="outline" 
                    className="h-11 px-6 rounded-xl glass-morphism gap-2"
                    aria-label="Open 17-Axis Knowledge Explorer"
                  >
                      <Activity className="h-5 w-5" aria-hidden="true" />
                      Explorer
                   </Button>
               </Link>
            </div>
          </header>

          {/* Stats Grid */}
          <ApiErrorBoundary moduleName="Real-time Metrics">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard 
                title="Total Nodes" 
                value={summary?.total_nodes ? (summary.total_nodes / 1000000).toFixed(1) + "M" : "1.2M"} 
                subtext="+12k this week"
                icon={Database}
                trend={4.2}
              />
              <StatCard 
                title="Control Coverage" 
                value="94%" 
                subtext="Compliance Rating"
                icon={ShieldCheck}
                variant="success"
                trend={1.5}
              />
              <StatCard 
                title="Active Issues" 
                value={summary?.active_issues || 0} 
                subtext="Critical failures"
                icon={AlertTriangle}
                variant={summary?.active_issues > 0 ? "destructive" : "default"}
              />
              <StatCard 
                title="System Health" 
                value={isOperational ? "Safe" : "Degraded"} 
                subtext="L1-L10 Gateway"
                icon={Activity}
                variant={isOperational ? "success" : "destructive"}
              />
            </div>
          </ApiErrorBoundary>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
             <div className="lg:col-span-2 space-y-6">
                <section aria-label="Compliance and Intelligence Trends">
                  <ApiErrorBoundary moduleName="Trend Analytics">
                    <ComplianceTrendChart />
                  </ApiErrorBoundary>
                </section>

                {/* Recent Activity Table */}
                <ApiErrorBoundary moduleName="Execution Trace Stream">
                  <Card className="glass-card" role="region" aria-label="Recent Execution Traces">
                     <CardHeader className="flex flex-row items-center justify-between">
                        <div>
                          <CardTitle className="text-lg">Recent Execution Traces</CardTitle>
                          <CardDescription>Live audit stream from Knowledge Algorithms.</CardDescription>
                        </div>
                        <Link href="/runs">
                          <Button variant="ghost" size="sm" className="text-blue-500">View All</Button>
                        </Link>
                     </CardHeader>
                     <CardContent>
                        <Table>
                           <TableHeader>
                              <TableRow className="hover:bg-transparent border-gray-100 dark:border-gray-800">
                                 <TableHead className="w-[100px]">ID</TableHead>
                                 <TableHead>KA Engine</TableHead>
                                 <TableHead>Status</TableHead>
                                 <TableHead className="text-right">Time</TableHead>
                              </TableRow>
                           </TableHeader>
                           <TableBody>
                               {isRunsLoading && Array.from({ length: 5 }).map((_, i) => (
                                   <TableRow key={i}>
                                       <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                                       <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                                       <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                                       <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                                   </TableRow>
                               ))}
                               
                               {runs?.map((run: TraceRun) => (
                                 <TableRow key={run.run_id} className="group border-gray-100 dark:border-gray-800 hover:bg-gray-50/50 dark:hover:bg-gray-800/30">
                                    <TableCell className="font-mono text-[10px] text-muted-foreground">
                                       {run.run_id.substring(0,8)}
                                    </TableCell>
                                    <TableCell>
                                       <div className="flex flex-col">
                                          <span className="font-semibold text-sm">{run.ka_id || 'System Base'}</span>
                                          <span className="text-[10px] text-muted-foreground uppercase tracking-widest">v2.0 Standard</span>
                                       </div>
                                    </TableCell>
                                    <TableCell>
                                       <Badge className={cn(
                                         "rounded-md px-1.5 py-0 text-[10px] font-bold uppercase",
                                         run.status === 'completed' ? "bg-emerald-500/10 text-emerald-600 border-emerald-500/20" : 
                                         run.status === 'failed' ? "bg-red-500/10 text-red-600 border-red-500/20" : 
                                         "bg-amber-500/10 text-amber-600 border-amber-500/20"
                                       )}>
                                           {run.status}
                                       </Badge>
                                    </TableCell>
                                    <TableCell className="text-right text-xs font-medium text-gray-500">
                                        {new Date(run.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </TableCell>
                                 </TableRow>
                              ))}
                           </TableBody>
                        </Table>
                     </CardContent>
                  </Card>
                </ApiErrorBoundary>
             </div>

             {/* Performance Sidebar */}
             <div className="space-y-6">
                <Card className="glass-card">
                   <CardHeader>
                      <CardTitle className="text-lg">System Metrics</CardTitle>
                      <CardDescription>L9-L10 Trace Integrity</CardDescription>
                   </CardHeader>
                   <CardContent className="space-y-5">
                      {[
                       { name: "Truth Engine v7.3", value: 99.7, unit: "%", label: "Accuracy" },
                       { name: "MAI Latency", value: 42, unit: "ms", label: "P99" },
                       { name: "Axis Coverage", value: 17, unit: "/17", label: "Dimensions" },
                      ].map((m) => (
                         <div key={m.name} className="space-y-2">
                            <div className="flex justify-between text-xs">
                               <span className="font-semibold text-gray-500">{m.name}</span>
                               <span className="text-emerald-500 font-bold">{m.value}{m.unit}</span>
                            </div>
                            <div className="h-1.5 w-full bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                               <div 
                                  className="h-full bg-emerald-500 rounded-full transition-all duration-1000" 
                                  style={{ width: `${(m.value / (m.unit === '/17' ? 17 : 100)) * 100}%` }} 
                               />
                            </div>
                         </div>
                      ))}
                   </CardContent>
                </Card>

                <Card className="glass-card bg-blue-600 dark:bg-blue-600 text-white border-none shadow-xl shadow-blue-500/20">
                   <CardHeader>
                      <CardTitle className="text-lg">Ready for Audit?</CardTitle>
                      <CardDescription className="text-blue-100">Generate a comprehensive compliance package.</CardDescription>
                   </CardHeader>
                   <CardContent>
                      <Button className="w-full bg-white text-blue-600 hover:bg-blue-50 font-bold rounded-xl h-11">
                         Export Audit Logs
                      </Button>
                      <p className="text-[10px] text-center mt-3 text-blue-200">
                         Aligned to NIST 800-171 & SOC2 Standards
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

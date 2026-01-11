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
import { 
  Activity, 
  Database, 
  Server, 
  Zap, 
  Users, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  ExternalLink,
  PlayCircle,
  MessageSquarePlus
} from 'lucide-react';

export default function DashboardPage() {
  // Data Fetching with SWR (Stale-While-Revalidate)
  const { data: runs, isLoading: isRunsLoading } = useSWR('trace-list', () => api.trace.list(5), { 
    refreshInterval: 5000,
    fallbackData: []
  });

  const { data: systemStatus, isLoading: isStatusLoading } = useSWR<string>('system-health', () => api.system.health(), {
    refreshInterval: 10000,
    fallbackData: 'Checking...'
  });

  // Derived State
  const isOperational = systemStatus === 'Operational' || systemStatus === 'ok';

  return (
    <main className="min-h-screen bg-muted/40 p-6 md:p-8">
      <div className="container mx-auto max-w-7xl space-y-8">
        
        {/* Header Section */}
        <header className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground">
              Real-time overview of Universal Knowledge Graph performance.
            </p>
          </div>
          <div className="flex gap-2">
             <Link href="/chat">
                <Button className="gap-2">
                  <MessageSquarePlus className="h-4 w-4" />
                  New Chat Session
                </Button>
             </Link>
             <Link href="/simulations">
                 <Button variant="outline" className="gap-2">
                    <PlayCircle className="h-4 w-4" />
                    Run Simulation
                 </Button>
             </Link>
          </div>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Nodes</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">1.2M</div>
              <p className="text-xs text-muted-foreground mt-1">+12% from last month</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">24</div>
              <p className="text-xs text-muted-foreground mt-1">Across 6 pillars</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Health</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {isStatusLoading ? (
                 <Skeleton className="h-8 w-24" /> 
              ) : (
                <div className={cn("text-2xl font-bold flex items-center gap-2", isOperational ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600")}>
                    {isOperational ? (
                      <>Operational <CheckCircle className="h-5 w-5" /></>
                    ) : (
                      <>{systemStatus} <AlertCircle className="h-5 w-5" /></>
                    )}
                </div>
              )}
              <p className="text-xs text-muted-foreground mt-1">Gateway Status</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Recent Activity</CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              {isRunsLoading ? (
                <Skeleton className="h-8 w-12" />
              ) : (
                <div className="text-2xl font-bold">{runs?.length || 0}</div>
              )}
              <p className="text-xs text-muted-foreground mt-1">Events in last 5m</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
           {/* Recent Trace Activity Table */}
           <Card className="lg:col-span-2">
              <CardHeader>
                 <CardTitle className="flex items-center gap-2">
                    <Clock className="h-5 w-5 text-muted-foreground" />
                    Recent Trace Execution
                 </CardTitle>
                 <CardDescription>Live execution logs from the Knowledge Graph engine.</CardDescription>
              </CardHeader>
              <CardContent>
                 <Table>
                    <TableHeader>
                       <TableRow>
                          <TableHead>Run ID</TableHead>
                          <TableHead>KA / Context</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead className="text-right">Timestamp</TableHead>
                       </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isRunsLoading && Array.from({ length: 5 }).map((_, i) => (
                            <TableRow key={i}>
                                <TableCell><Skeleton className="h-4 w-20" /></TableCell>
                                <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                                <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                                <TableCell className="text-right"><Skeleton className="h-4 w-24 ml-auto" /></TableCell>
                            </TableRow>
                        ))}
                        
                        {!isRunsLoading && runs?.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center py-12 text-muted-foreground">
                                    No recent activity found. Start a new chat session to generate traces.
                                </TableCell>
                            </TableRow>
                        )}

                        {runs?.map((run: any) => (
                          <TableRow key={run.run_id} className="group">
                             <TableCell className="font-mono text-xs font-medium text-muted-foreground group-hover:text-primary transition-colors">
                                {run.run_id.substring(0,8)}
                             </TableCell>
                             <TableCell className="font-medium">
                                {run.ka_id || 'General Chat'}
                             </TableCell>
                             <TableCell>
                                <Badge variant={run.status === 'completed' ? 'default' : run.status === 'failed' ? 'destructive' : 'secondary'}>
                                    {run.status}
                                </Badge>
                             </TableCell>
                             <TableCell className="text-right text-xs text-muted-foreground">
                                 {new Date(run.created_at).toLocaleTimeString()}
                             </TableCell>
                          </TableRow>
                       ))}
                    </TableBody>
                 </Table>
              </CardContent>
           </Card>

           {/* Service Status Panel */}
           <Card>
              <CardHeader>
                 <CardTitle className="flex items-center gap-2">
                    <Server className="h-5 w-5 text-muted-foreground" />
                    System Status
                 </CardTitle>
                 <CardDescription>Component health check.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                 <div className="space-y-4">
                    {[
                       { name: "LLM Gateway", status: isOperational ? 'Operational' : systemStatus, statusColor: isOperational ? "bg-emerald-500" : "bg-red-500" },
                       { name: "PostgreSQL Database", status: "Operational", statusColor: "bg-emerald-500" },
                       { name: "MCP Server Registry", status: "Operational", statusColor: "bg-emerald-500" },
                       { name: "Redis Cache", status: "Operational", statusColor: "bg-emerald-500" },
                    ].map((svc) => (
                       <div key={svc.name} className="flex items-center justify-between p-3 rounded-lg border bg-card/50">
                          <div className="flex items-center gap-3">
                             <div className={cn("w-2.5 h-2.5 rounded-full ring-2 ring-offset-2 ring-offset-background", svc.statusColor)} />
                             <span className="text-sm font-medium">{svc.name}</span>
                          </div>
                          <span className="text-xs text-muted-foreground">{svc.status}</span>
                       </div>
                    ))}
                 </div>
                 
                 <div className="pt-2">
                     <Link href="/runs" className="w-full">
                        <Button className="w-full gap-2" variant="outline">
                           View All Traces
                           <ExternalLink className="h-4 w-4" />
                        </Button>
                     </Link>
                 </div>
              </CardContent>
           </Card>
        </div>
      </div>
    </main>
  );
}

'use client';

import { useState, useEffect } from 'react';
import Link from "next/link";
import { api, TraceRun } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

export default function DashboardPage() {
  const [runs, setRuns] = useState<TraceRun[]>([]);
  const [systemStatus, setSystemStatus] = useState<string>('Checking...');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
     let mounted = true;
     
     async function fetchData() {
         try {
             // Parallel fetch
             const [runsData, healthData] = await Promise.all([
                 api.trace.list(5),
                 api.system.health()
             ]);
             
             if (mounted) {
                 setRuns(runsData || []);
                 setSystemStatus(healthData);
                 setIsLoading(false);
             }
         } catch (e) {
             console.error("Dashboard fetch error", e);
             if (mounted) setIsLoading(false);
         }
     }

     fetchData();
     
     // Poll every 10s
     const interval = setInterval(fetchData, 10000);
     return () => { mounted = false; clearInterval(interval); };
  }, []);

  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8">
      <div className="container mx-auto max-w-7xl">
        <header className="mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
            <p className="text-gray-500 dark:text-gray-400">Overview of system performance and knowledge graph status.</p>
          </div>
          <div className="flex gap-2">
             <Link href="/chat">
                <Button>New Chat Session</Button>
             </Link>
             <Link href="/simulations">
                 <Button variant="outline">Run Simulation</Button>
             </Link>
          </div>
        </header>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Nodes</CardTitle>
              <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">1.2M</div>
              <p className="text-xs text-green-500 font-medium">+12% from last month</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Agents</CardTitle>
               <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">24</div>
              <p className="text-xs text-gray-500">Across 6 pillars</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Health</CardTitle>
               <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className={cn("text-2xl font-bold", systemStatus === 'Operational' ? "text-green-600" : "text-yellow-600")}>
                  {systemStatus}
              </div>
              <p className="text-xs text-gray-500">Gateway Status</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Recent Traces</CardTitle>
               <svg className="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{runs.length}</div>
              <p className="text-xs text-gray-500">Last 5 fetches</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
           {/* Recent Activity */}
           <Card className="lg:col-span-2">
              <CardHeader>
                 <CardTitle>Recent Trace Activity</CardTitle>
                 <CardDescription>Real-time execution logs from the Knowledge Graph.</CardDescription>
              </CardHeader>
              <CardContent>
                 <Table>
                    <TableHeader>
                       <TableRow>
                          <TableHead>Run ID</TableHead>
                          <TableHead>KA / Type</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead className="text-right">Created</TableHead>
                       </TableRow>
                    </TableHeader>
                    <TableBody>
                        {isLoading && (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center py-8 text-gray-500">
                                    Loading traces...
                                </TableCell>
                            </TableRow>
                        )}
                        {!isLoading && runs.length === 0 && (
                            <TableRow>
                                <TableCell colSpan={4} className="text-center py-8 text-gray-500">
                                    No recent activity found. Start a chat!
                                </TableCell>
                            </TableRow>
                        )}
                        {runs.map((run) => (
                          <TableRow key={run.run_id}>
                             <TableCell className="font-mono text-xs">{run.run_id.substring(0,8)}</TableCell>
                             <TableCell>{run.ka_id || 'General Chat'}</TableCell>
                             <TableCell>
                                <Badge variant={run.status === 'completed' ? 'success' : run.status === 'failed' ? 'destructive' : 'secondary'}>
                                    {run.status}
                                </Badge>
                             </TableCell>
                             <TableCell className="text-right text-gray-500 text-xs">
                                 {new Date(run.created_at).toLocaleTimeString()}
                             </TableCell>
                          </TableRow>
                       ))}
                    </TableBody>
                 </Table>
              </CardContent>
           </Card>

           {/* System Status */}
           <Card>
              <CardHeader>
                 <CardTitle>Service Status</CardTitle>
                 <CardDescription>Live health check.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                 {[
                    { name: "LLM Gateway", status: systemStatus, color: systemStatus === 'Operational' ? "bg-green-500" : "bg-red-500" },
                    { name: "PostgreSQL DB", status: "Operational", color: "bg-green-500" },
                    { name: "MCP Server", status: "Operational", color: "bg-green-500" },
                 ].map((svc) => (
                    <div key={svc.name} className="flex items-center justify-between p-2 rounded-lg bg-gray-50 dark:bg-gray-800">
                       <span className="font-medium">{svc.name}</span>
                       <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${svc.color}`}></span>
                          <span className="text-xs text-gray-500">{svc.status}</span>
                       </div>
                    </div>
                 ))}
                 <div className="pt-4">
                     <Link href="/runs">
                        <Button className="w-full" variant="outline">View All Traces</Button>
                     </Link>
                 </div>
              </CardContent>
           </Card>
        </div>
      </div>
    </main>
  );
}

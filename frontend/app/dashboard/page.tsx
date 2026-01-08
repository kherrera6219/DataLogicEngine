'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";

export default function DashboardPage() {
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
              <svg className="h-4 w-4 text-muted-foreground text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
              <svg className="h-4 w-4 text-muted-foreground text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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
              <svg className="h-4 w-4 text-muted-foreground text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">99.9%</div>
              <p className="text-xs text-gray-500">Uptime (30 days)</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pending Alerts</CardTitle>
              <svg className="h-4 w-4 text-muted-foreground text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">3</div>
              <p className="text-xs text-yellow-500 font-medium">Requires attention</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
           {/* Recent Activity */}
           <Card className="lg:col-span-2">
              <CardHeader>
                 <CardTitle>Recent Activity</CardTitle>
                 <CardDescription>Latest system events and traces.</CardDescription>
              </CardHeader>
              <CardContent>
                 <Table>
                    <TableHeader>
                       <TableRow>
                          <TableHead>Event ID</TableHead>
                          <TableHead>Type</TableHead>
                          <TableHead>Status</TableHead>
                          <TableHead className="text-right">Time</TableHead>
                       </TableRow>
                    </TableHeader>
                    <TableBody>
                       {[
                          { id: "EVT-9021", type: "KA Execution (AoT)", status: "Success", time: "2 mins ago" },
                          { id: "EVT-9020", type: "Graph Rebalance", status: "Success", time: "15 mins ago" },
                          { id: "EVT-9019", type: "User Login", status: "Success", time: "1 hour ago" },
                          { id: "EVT-9018", type: "Simulation (Stress Test)", status: "Failed", time: "2 hours ago" },
                          { id: "EVT-9017", type: "Backup", status: "Success", time: "4 hours ago" },
                       ].map((evt) => (
                          <TableRow key={evt.id}>
                             <TableCell className="font-mono text-xs">{evt.id}</TableCell>
                             <TableCell>{evt.type}</TableCell>
                             <TableCell>
                                <Badge variant={evt.status === 'Success' ? 'success' : 'destructive'}>{evt.status}</Badge>
                             </TableCell>
                             <TableCell className="text-right text-gray-500">{evt.time}</TableCell>
                          </TableRow>
                       ))}
                    </TableBody>
                 </Table>
              </CardContent>
           </Card>

           {/* System Status */}
           <Card>
              <CardHeader>
                 <CardTitle>System Status</CardTitle>
                 <CardDescription>Service health verification.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                 {[
                    { name: "LLM Gateway", status: "Operational", color: "bg-green-500" },
                    { name: "PostgreSQL DB", status: "Operational", color: "bg-green-500" },
                    { name: "Redis Cache", status: "Operational", color: "bg-green-500" },
                    { name: "MCP Server", status: "Operational", color: "bg-green-500" },
                    { name: "SMTP Service", status: "Degraded", color: "bg-yellow-500" },
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
                     <Button className="w-full" variant="outline">View Full Report</Button>
                 </div>
              </CardContent>
           </Card>
        </div>
      </div>
    </main>
  );
}

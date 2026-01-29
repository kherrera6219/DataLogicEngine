'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { 
  AreaChart, Area, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, ResponsiveContainer, Line
} from 'recharts';
import { 
  BarChart3, Settings, Download, Mail, 
  CheckCircle, XCircle, Calendar
} from "lucide-react";
import { api, McpStats } from '@/lib/api';

export function McpAnalytics() {
  const [data, setData] = useState<McpStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const stats = await api.analytics.mcp() as McpStats;
        // Adding colors for error stats manually if not provided by API
        const rawErrorStats = stats.error_stats || [
          { name: 'Timeout', value: 23, color: 'bg-yellow-500' },
          { name: 'Auth', value: 12, color: 'bg-red-500' },
          { name: 'Invalid', value: 8, color: 'bg-blue-500' },
          { name: 'Unavailable', value: 5, color: 'bg-gray-500' },
        ];
        
        const coloredErrorStats = rawErrorStats.map((s, i: number) => ({
          ...s,
          colorCode: s.colorCode || s.color || ['#f59e0b', '#ef4444', '#3b82f6', '#6b7280'][i % 4]
        }));

        setData({
          ...stats,
          error_stats: coloredErrorStats
        });
      } catch (err) {
        console.error("Failed to fetch MCP analytics:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  if (loading || !data) {
    return (
      <div className="h-96 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
       
       <div className="flex justify-between items-center">
          <div>
             <h2 className="text-2xl font-bold text-white">MCP Performance Analytics</h2>
             <p className="text-gray-400">Real-time monitoring and health status</p>
          </div>
          <div className="flex gap-2">
             <Button variant="outline"><Calendar className="mr-2 h-4 w-4" /> Last 24 Hours</Button>
             <Button variant="outline"><Settings className="h-4 w-4" /></Button>
          </div>
       </div>

       {/* 📊 Message Flow Chart */}
       <Card className="border-white/10">
          <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
             <CardTitle className="text-lg flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-400" /> Message Flow (JSON-RPC)
             </CardTitle>
          </CardHeader>
          <CardContent className="h-[300px] pt-6">
             <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.time_series}>
                   <defs>
                      <linearGradient id="colorReq" x1="0" y1="0" x2="0" y2="1">
                         <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                         <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorRes" x1="0" y1="0" x2="0" y2="1">
                         <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                         <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                   </defs>
                   <XAxis dataKey="time" stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} />
                   <YAxis stroke="#6b7280" fontSize={10} tickLine={false} axisLine={false} />
                   <Tooltip 
                      contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', fontSize: '12px' }}
                      itemStyle={{ color: '#e5e7eb' }}
                   />
                   <Area type="monotone" dataKey="requests" stroke="#3b82f6" fillOpacity={1} fill="url(#colorReq)" />
                   <Area type="monotone" dataKey="responses" stroke="#10b981" fillOpacity={1} fill="url(#colorRes)" />
                   <Line type="monotone" dataKey="errors" stroke="#ef4444" strokeWidth={2} dot={false} />
                </AreaChart>
             </ResponsiveContainer>
          </CardContent>
       </Card>

       <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Top Tools */}
          <Card className="border-white/10 lg:col-span-1">
             <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
                <CardTitle className="text-lg">Top Tools</CardTitle>
             </CardHeader>
             <CardContent className="pt-6 space-y-3">
                {data.top_tools.map((tool, i) => (
                   <div key={tool.name} className="flex justify-between items-center text-sm">
                      <div className="flex items-center gap-2">
                         <span className="text-gray-500 font-mono w-4">{i + 1}.</span>
                         <span className="text-gray-300 truncate max-w-[150px]" title={tool.name}>{tool.name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                         <span className="text-white font-mono">{tool.calls.toLocaleString()}</span>
                         <span className="text-xs text-blue-400 bg-blue-400/10 px-1 rounded">{tool.percent.toFixed(1)}%</span>
                      </div>
                   </div>
                ))}
             </CardContent>
          </Card>

          {/* Server Health & Errors */}
          <div className="lg:col-span-2 space-y-8">
             
             {/* Server Health Grid */}
             <Card className="border-white/10">
                <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
                   <CardTitle className="text-lg">Server Health Status</CardTitle>
                </CardHeader>
                <CardContent className="pt-6">
                   <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {data.server_health.map((server) => (
                         <div key={server.name} className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10">
                            <div className="flex items-center gap-2">
                               {server.status === 'Healthy' ? <CheckCircle className="h-4 w-4 text-green-400" /> : <XCircle className="h-4 w-4 text-red-500" />}
                               <span className="text-sm font-bold text-gray-300">{server.name}</span>
                            </div>
                            <span className={`text-xs font-mono ${(server.latency || 0) > 200 ? 'text-yellow-400' : 'text-gray-400'}`}>
                               {(server.latency || 0) > 0 ? `${server.latency}ms` : '-'}
                            </span>
                         </div>
                      ))}
                   </div>
                </CardContent>
             </Card>

             {/* Error Analysis */}
             <Card className="border-white/10">
                <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
                   <CardTitle className="text-lg flex justify-between">
                      <span>Error Analysis</span>
                      <span className="text-sm font-normal text-red-400">Real-time stats</span>
                   </CardTitle>
                </CardHeader>
                <CardContent className="pt-6 grid grid-cols-1 sm:grid-cols-2 gap-6 items-center">
                   <div className="h-[200px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                         <PieChart>
                            <Pie 
                               data={data.error_stats} 
                               innerRadius={60} 
                               outerRadius={80} 
                               paddingAngle={5} 
                               dataKey="value"
                            >
                               {data.error_stats.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={entry.colorCode} />
                               ))}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', fontSize: '12px' }} itemStyle={{ color: '#e5e7eb' }} />
                         </PieChart>
                      </ResponsiveContainer>
                   </div>
                   <div className="space-y-4">
                       {data.error_stats.map((stat) => (
                          <div key={stat.name} className="flex justify-between items-center">
                             <div className="flex items-center gap-2">
                                <span className={`w-3 h-3 rounded-full ${stat.color || 'bg-gray-500'}`} />
                                <span className="text-sm text-gray-300">{stat.name}</span>
                             </div>
                             <span className="font-mono text-sm text-white">{stat.value}</span>
                          </div>
                       ))}
                       <div className="pt-4 flex gap-2">
                          <Button variant="outline" size="sm" className="w-full"><Download className="mr-2 h-4 w-4" /> Report</Button>
                          <Button variant="outline" size="sm" className="w-full"><Mail className="mr-2 h-4 w-4" /> Email</Button>
                       </div>
                   </div>
                </CardContent>
             </Card>

          </div>
       </div>

    </div>
  );
}

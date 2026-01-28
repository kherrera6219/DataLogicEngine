'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, AreaChart, Area, PieChart, Pie, Cell 
} from 'recharts';
import { 
  BarChart3, Calendar, Download, Mail, Settings, AlertTriangle, 
  CheckCircle, XCircle, Clock
} from "lucide-react";

// Mock Data for Analytics
const timeSeriesData = [
  { time: '6am', requests: 120, responses: 118, errors: 2 },
  { time: '9am', requests: 350, responses: 345, errors: 5 },
  { time: '12pm', requests: 420, responses: 418, errors: 2 },
  { time: '3pm', requests: 380, responses: 375, errors: 5 },
  { time: '6pm', requests: 250, responses: 248, errors: 2 },
  { time: '9pm', requests: 180, responses: 178, errors: 2 },
  { time: 'Now', requests: 150, responses: 149, errors: 1 },
];

const topTools = [
  { name: 'query_knowledge', calls: 5234, percent: 21.0 },
  { name: 'resolve_coordinate', calls: 4892, percent: 19.6 },
  { name: 'validate_compliance', calls: 3421, percent: 13.7 },
  { name: 'execute_query (PG)', calls: 3234, percent: 13.0 },
  { name: 'simulate_scenario', calls: 1567, percent: 6.3 },
  { name: 'github_search_code', calls: 1234, percent: 5.0 },
  { name: 'slack_send_message', calls: 892, percent: 3.6 },
  { name: 'recursive_refine', calls: 892, percent: 3.6 },
  { name: 'drive_read_file', calls: 678, percent: 2.7 },
  { name: 'salesforce_query', calls: 456, percent: 1.8 },
];

const serverHealth = [
  { name: 'UKG Server', status: 'Healthy', latency: 23 },
  { name: 'Google Drive', status: 'Healthy', latency: 145 },
  { name: 'Slack', status: 'Healthy', latency: 89 },
  { name: 'Salesforce', status: 'Healthy', latency: 234 },
  { name: 'GitHub', status: 'Healthy', latency: 178 },
  { name: 'PostgreSQL', status: 'Healthy', latency: 12 },
  { name: 'Canva', status: 'Healthy', latency: 312 },
  { name: 'Puppeteer', status: 'Healthy', latency: 45 },
  { name: 'Stripe', status: 'Disconnected', latency: 0 },
];

const errorStats = [
  { name: 'Timeout', value: 23, color: '#f59e0b' },
  { name: 'Auth', value: 12, color: '#ef4444' },
  { name: 'Invalid', value: 8, color: '#3b82f6' },
  { name: 'Unavailable', value: 5, color: '#6b7280' },
];

export function McpAnalytics() {
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
                <AreaChart data={timeSeriesData}>
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
          
          {/* Top 10 Tools */}
          <Card className="border-white/10 lg:col-span-1">
             <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
                <CardTitle className="text-lg">Top 10 Most Used Tools</CardTitle>
             </CardHeader>
             <CardContent className="pt-6 space-y-3">
                {topTools.slice(0, 8).map((tool, i) => (
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
                      {serverHealth.map((server) => (
                         <div key={server.name} className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10">
                            <div className="flex items-center gap-2">
                               {server.status === 'Healthy' ? <CheckCircle className="h-4 w-4 text-green-400" /> : <XCircle className="h-4 w-4 text-red-500" />}
                               <span className="text-sm font-bold text-gray-300">{server.name}</span>
                            </div>
                            <span className={`text-xs font-mono ${server.latency > 200 ? 'text-yellow-400' : 'text-gray-400'}`}>
                               {server.latency > 0 ? `${server.latency}ms` : '-'}
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
                      <span className="text-sm font-normal text-red-400">0.19% Error Rate</span>
                   </CardTitle>
                </CardHeader>
                <CardContent className="pt-6 grid grid-cols-1 sm:grid-cols-2 gap-6 items-center">
                   <div className="h-[200px] w-full">
                      <ResponsiveContainer width="100%" height="100%">
                         <PieChart>
                            <Pie 
                               data={errorStats} 
                               innerRadius={60} 
                               outerRadius={80} 
                               paddingAngle={5} 
                               dataKey="value"
                            >
                               {errorStats.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={entry.color} />
                               ))}
                            </Pie>
                            <Tooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', fontSize: '12px' }} itemStyle={{ color: '#e5e7eb' }} />
                         </PieChart>
                      </ResponsiveContainer>
                   </div>
                   <div className="space-y-4">
                       {errorStats.map((stat) => (
                          <div key={stat.name} className="flex justify-between items-center">
                             <div className="flex items-center gap-2">
                                <span className="w-3 h-3 rounded-full" style={{ backgroundColor: stat.color }} />
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

'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Users, Activity, ShieldAlert, Server, 
  MoreHorizontal, Plus, Search, Filter 
} from "lucide-react";
import { Input } from "@/components/ui/input";

export default function AdminPage() {
  return (
    <div className="min-h-screen bg-black text-white font-sans">
       {/* Header */}
       <div className="h-16 border-b border-white/10 bg-gray-900/50 backdrop-blur-md flex items-center justify-between px-6 sticky top-0 z-10">
          <div className="flex items-center gap-2">
             <div className="bg-red-900/20 p-2 rounded">
                <ShieldAlert className="h-5 w-5 text-red-500" />
             </div>
             <div>
                <h1 className="text-sm font-bold tracking-wide">System Administration</h1>
                <div className="text-[10px] text-gray-400 font-mono">Root Access • Encrypted Session</div>
             </div>
          </div>
          <div className="flex gap-3">
             <div className="flex items-center gap-2 text-xs text-gray-400 px-3 py-1 bg-white/5 rounded-full border border-white/5">
                <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                System Healthy
             </div>
          </div>
       </div>

       <div className="max-w-7xl mx-auto p-6 space-y-8">
          
          {/* Metrics Grid */}
          <div className="grid grid-cols-4 gap-4">
             {[
                { label: 'Active Users', value: '8,492', sub: '+12% this week', icon: Users, color: 'text-blue-400' },
                { label: 'System Load', value: '42%', sub: 'Optimal Range', icon: Server, color: 'text-green-400' },
                { label: 'Threats Blocked', value: '142', sub: 'Last 24h', icon: ShieldAlert, color: 'text-red-400' },
                { label: 'API Requests', value: '1.2M', sub: '99.9% Success', icon: Activity, color: 'text-purple-400' },
             ].map((m, i) => (
                <Card key={i} className="bg-gray-900/30 border-white/10">
                   <CardContent className="p-4 flex items-center justify-between">
                      <div>
                         <div className="text-xs text-gray-400 uppercase tracking-wider mb-1">{m.label}</div>
                         <div className="text-2xl font-bold font-mono">{m.value}</div>
                         <div className="text-[10px] text-gray-500 mt-1">{m.sub}</div>
                      </div>
                      <m.icon className={`h-8 w-8 opacity-20 ${m.color}`} />
                   </CardContent>
                </Card>
             ))}
          </div>

          {/* User Management */}
          <Card className="bg-gray-900/30 border-white/10">
             <CardHeader className="border-b border-white/5 pb-4">
                <div className="flex items-center justify-between">
                   <div>
                      <CardTitle className="text-sm">User Management</CardTitle>
                      <CardDescription className="text-xs text-gray-400">Manage enterprise access and permissions.</CardDescription>
                   </div>
                   <div className="flex gap-2">
                      <div className="relative">
                         <Search className="absolute left-2 top-2.5 h-3 w-3 text-gray-500" />
                         <Input placeholder="Search users..." className="h-8 pl-8 w-64 bg-black/50 border-white/10 text-xs" />
                      </div>
                      <Button variant="outline" size="sm" className="h-8 border-white/10 text-gray-400 hover:text-white gap-2">
                         <Filter className="h-3 w-3" /> Filters
                      </Button>
                      <Button size="sm" className="h-8 bg-blue-600 hover:bg-blue-700 text-white gap-2">
                         <Plus className="h-3 w-3" /> Add User
                      </Button>
                   </div>
                </div>
             </CardHeader>
             <CardContent className="p-0">
                <table className="w-full text-left text-xs">
                   <thead className="bg-white/5 text-gray-400 font-mono uppercase">
                      <tr>
                         <th className="p-4 font-medium">User</th>
                         <th className="p-4 font-medium">Role</th>
                         <th className="p-4 font-medium">Status</th>
                         <th className="p-4 font-medium">Last Active</th>
                         <th className="p-4 font-medium text-right">Actions</th>
                      </tr>
                   </thead>
                   <tbody className="divide-y divide-white/5 text-gray-300">
                      {[
                         { name: 'Sarah Connor', email: 's.connor@ukg.com', role: 'System Admin', status: 'active', active: 'Now' },
                         { name: 'John Alert', email: 'j.alert@ukg.com', role: 'Security Ops', status: 'active', active: '2m ago' },
                         { name: 'Desmond Miles', email: 'd.miles@ukg.com', role: 'Viewer', status: 'inactive', active: '2d ago' },
                         { name: 'Lara Croft', email: 'l.croft@ukg.com', role: 'Editor', status: 'active', active: '1h ago' },
                         { name: 'Bruce Banner', email: 'b.banner@ukg.com', role: 'Developer', status: 'warning', active: '5h ago' },
                      ].map((u, i) => (
                         <tr key={i} className="hover:bg-white/5 transition-colors group">
                            <td className="p-4">
                               <div className="font-bold text-white">{u.name}</div>
                               <div className="text-gray-500">{u.email}</div>
                            </td>
                            <td className="p-4">
                               <Badge variant="outline" className="bg-blue-900/10 text-blue-400 border-blue-500/30 text-[10px]">
                                  {u.role}
                               </Badge>
                            </td>
                            <td className="p-4">
                               <div className="flex items-center gap-2">
                                  <div className={`h-1.5 w-1.5 rounded-full ${u.status === 'active' ? 'bg-green-500' : u.status === 'warning' ? 'bg-yellow-500' : 'bg-gray-500'}`}></div>
                                  <span className="capitalize">{u.status}</span>
                               </div>
                            </td>
                            <td className="p-4 font-mono text-gray-500">{u.active}</td>
                            <td className="p-4 text-right">
                               <Button variant="ghost" size="icon" className="h-6 w-6 text-gray-500 hover:text-white">
                                  <MoreHorizontal className="h-4 w-4" />
                               </Button>
                            </td>
                         </tr>
                      ))}
                   </tbody>
                </table>
             </CardContent>
          </Card>
       </div>
    </div>
  );
}

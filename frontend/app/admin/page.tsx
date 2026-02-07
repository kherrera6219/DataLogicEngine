'use client';

import React, { useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Users, Activity, ShieldAlert, Server, 
  MoreHorizontal, Plus, Search, Filter 
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

export default function AdminPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const isAdmin = Boolean(user?.is_admin || user?.role === 'admin' || user?.role === 'owner');

  useEffect(() => {
    if (!isLoading && !isAdmin) {
      router.replace('/dashboard?error=admin_required');
    }
  }, [isAdmin, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-foreground">
        <p className="text-sm text-muted-foreground">Checking administrative access...</p>
      </div>
    );
  }

  if (!isAdmin) {
    return null;
  }

  return (
    <div className="min-h-full bg-[#111111] text-white font-sans">
      <div className="min-h-full bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">
         {/* Header */}
         <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center justify-between px-8 backdrop-blur-3xl">
            <div className="flex items-center gap-3">
               <div className="bg-red-900/10 p-2 rounded-lg border border-red-500/20">
                  <ShieldAlert className="h-5 w-5 text-red-500" />
               </div>
               <div>
                  <h1 className="text-title font-bold text-gray-100">System Administration</h1>
                  <div className="text-[10px] text-gray-500 font-mono flex items-center gap-2">
                     ROOT_ACCCESS_GRANTED <span className="text-green-500">●</span> 
                  </div>
               </div>
            </div>
            <div className="flex gap-3">
               <div className="flex items-center gap-2 text-xs text-gray-400 px-3 py-1 bg-white/5 rounded-full border border-white/5">
                  <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse"></div>
                  System Healthy
               </div>
            </div>
         </div>

         <div className="max-w-[1600px] w-full mx-auto p-8 space-y-8 animate-connected-enter">
            
            {/* Metrics Grid */}
            <div className="grid grid-cols-4 gap-4">
               {[
                  { label: 'Active Users', value: '8,492', sub: '+12% this week', icon: Users, color: 'text-blue-400' },
                  { label: 'System Load', value: '42%', sub: 'Optimal Range', icon: Server, color: 'text-green-400' },
                  { label: 'Threats Blocked', value: '142', sub: 'Last 24h', icon: ShieldAlert, color: 'text-red-400' },
                  { label: 'API Requests', value: '1.2M', sub: '99.9% Success', icon: Activity, color: 'text-purple-400' },
               ].map((m, i) => (
                  <Card key={i} className="fluent-card hover:-translate-y-1">
                     <CardContent className="p-5 flex items-center justify-between">
                        <div>
                           <div className="text-xs text-gray-500 uppercase tracking-wider mb-1 font-semibold">{m.label}</div>
                           <div className="text-2xl font-bold font-mono text-gray-200">{m.value}</div>
                           <div className="text-[10px] text-gray-500 mt-1">{m.sub}</div>
                        </div>
                        <m.icon className={`h-8 w-8 opacity-20 ${m.color}`} />
                     </CardContent>
                  </Card>
               ))}
            </div>

            {/* User Management */}
            <Card className="fluent-card bg-[#1a1a1a] border-[#333]">
               <CardHeader className="border-b border-white/5 pb-4">
                  <div className="flex items-center justify-between">
                     <div>
                        <CardTitle className="text-base font-semibold text-gray-200">User Management</CardTitle>
                        <CardDescription className="text-xs text-gray-500 mt-1">Manage enterprise access keys and permissions.</CardDescription>
                     </div>
                     <div className="flex gap-2">
                        <div className="relative">
                           <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-gray-500" />
                           <Input placeholder="Search users..." className="h-9 pl-9 w-64 bg-black/20 border-white/10 text-sm focus:border-blue-500/50 transition-colors" />
                        </div>
                        <Button variant="outline" size="sm" className="h-9 border-white/10 text-gray-400 hover:text-white gap-2 bg-white/5">
                           <Filter className="h-3.5 w-3.5" /> Filters
                        </Button>
                        <Button size="sm" className="h-9 bg-blue-600 hover:bg-blue-700 text-white gap-2 shadow-lg shadow-blue-900/20">
                           <Plus className="h-3.5 w-3.5" /> Add User
                        </Button>
                     </div>
                  </div>
               </CardHeader>
               <CardContent className="p-0">
                  <table className="w-full text-left text-sm">
                     <thead className="bg-black/20 text-gray-500 font-medium border-b border-white/5">
                        <tr>
                           <th className="p-4 font-medium pl-6">User Identity</th>
                           <th className="p-4 font-medium">Role Access</th>
                           <th className="p-4 font-medium">Status</th>
                           <th className="p-4 font-medium">Last Active</th>
                           <th className="p-4 font-medium text-right pr-6">Actions</th>
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
                           <tr key={i} className="hover:bg-white/[0.02] transition-colors group">
                              <td className="p-4 pl-6">
                                 <div className="font-semibold text-gray-200">{u.name}</div>
                                 <div className="text-xs text-gray-500">{u.email}</div>
                              </td>
                              <td className="p-4">
                                 <Badge variant="outline" className="bg-blue-500/5 text-blue-400 border-blue-500/20 text-[10px] font-mono">
                                    {u.role}
                                 </Badge>
                              </td>
                              <td className="p-4">
                                 <div className="flex items-center gap-2">
                                    <div className={`h-1.5 w-1.5 rounded-full ${u.status === 'active' ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]' : u.status === 'warning' ? 'bg-yellow-500' : 'bg-gray-600'}`}></div>
                                    <span className="capitalize text-xs text-gray-400">{u.status}</span>
                                 </div>
                              </td>
                              <td className="p-4 font-mono text-xs text-gray-500">{u.active}</td>
                              <td className="p-4 text-right pr-6">
                                 <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-500 hover:text-white hover:bg-white/10 rounded-md">
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
    </div>
  );
}

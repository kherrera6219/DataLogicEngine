'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Folder, Plus, Search, Filter, MoreVertical, 
  Clock, FileText, Star, ShieldCheck, BarChart3, Users, Layers
} from "lucide-react";
import { Input } from "@/components/ui/input";

export default function ProjectsPage() {
  const projects = [
    { id: '1', title: 'HIPAA Compliance Audit', count: 12, updated: '2h ago', status: 'Active', color: 'bg-blue-600', icon: ShieldCheck },
    { id: '2', title: 'Q1 Financial Reports', count: 4, updated: '1d ago', status: 'Review', color: 'bg-green-600', icon: BarChart3 },
    { id: '3', title: 'Legal Contracts 2026', count: 28, updated: '4d ago', status: 'Archived', color: 'bg-gray-600', icon: FileText },
    { id: '4', title: 'Employee Handbook', count: 1, updated: '1w ago', status: 'Active', color: 'bg-purple-600', icon: Users },
    { id: '5', title: 'Project Titan Specs', count: 15, updated: '2w ago', status: 'In Progress', color: 'bg-orange-600', icon: Layers },
  ];

  return (
    <div className="flex-1 flex flex-col bg-transparent animate-in fade-in duration-700">
       
       {/* Acrylic Header */}
       <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center justify-between px-8">
          <div className="flex items-center gap-3">
             <div className="bg-blue-500/10 p-2 rounded-lg border border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.1)]">
                <Folder className="h-5 w-5 text-blue-400" />
             </div>
             <div>
                <h1 className="text-xl font-bold text-gray-100 tracking-tight">Projects</h1>
                <div className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">Workspace Manager</div>
             </div>
          </div>
          <Button className="bg-blue-600 hover:bg-blue-500 text-white font-bold shadow-lg shadow-blue-900/20 transition-all hover:scale-105 active:scale-95">
             <Plus className="h-4 w-4 mr-2" /> New Project
          </Button>
       </div>

       <div className="max-w-[1600px] w-full mx-auto p-8 space-y-8">
          
          {/* Toolbar */}
          <div className="flex items-center justify-between bg-white/5 p-2 rounded-2xl border border-white/5 backdrop-blur-md shadow-inner">
             <div className="relative w-96">
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
                <Input placeholder="Search projects..." className="pl-9 bg-black/20 border-transparent hover:bg-black/40 focus:bg-black/50 transition-colors h-9 text-sm" />
             </div>
             <div className="flex gap-2">
                <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hover:bg-white/5 h-8 text-xs px-3">
                   <Clock className="h-3.5 w-3.5 mr-2" /> Recent
                </Button>
                <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hover:bg-white/5 h-8 text-xs px-3">
                   <Star className="h-3.5 w-3.5 mr-2" /> Favorites
                </Button>
                <div className="w-px h-6 bg-white/10 mx-1 my-auto"></div>
                <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hover:bg-white/5 h-8 text-xs px-3">
                   <Filter className="h-3.5 w-3.5 mr-2" /> Filter
                </Button>
             </div>
          </div>

          {/* Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
             {projects.map((p, i) => (
                <Link href={`/projects/${p.id}`} key={p.id} className="block group">
                   <Card className="fluent-acrylic border-white/10 h-full transition-all duration-500 hover:-translate-y-2 relative overflow-hidden group hover:shadow-[0_20px_40px_rgba(0,0,0,0.4)]">
                      {/* Gradient Ambient Light */}
                      <div className={`absolute -top-24 -right-24 h-48 w-48 ${p.color} opacity-0 group-hover:opacity-10 transition-opacity blur-[60px] pointer-events-none`}></div>
                      
                      {/* Status Line */}
                      <div className={`absolute top-0 left-0 right-0 h-1 ${p.color} opacity-50`}></div>
                      
                      <CardContent className="p-6">
                         <div className="flex justify-between items-start mb-6">
                            <div className={`h-12 w-12 rounded-2xl ${p.color} bg-opacity-20 flex items-center justify-center border border-white/10 shadow-lg group-hover:scale-110 transition-transform duration-500`}>
                               <p.icon className={`h-6 w-6 ${p.color.replace('bg-', 'text-').replace('-600', '-400')}`} />
                            </div>
                            <Button variant="ghost" size="icon" className="h-8 w-8 -mr-2 text-gray-500 hover:text-white hover:bg-white/10 rounded-lg">
                               <MoreVertical className="h-4 w-4" />
                            </Button>
                         </div>
                         
                         <h3 className="font-bold text-xl mb-1 text-gray-100 group-hover:text-blue-400 transition-colors tracking-tight">{p.title}</h3>
                         <div className="flex items-center gap-2 mb-6">
                            <Badge className="bg-white/5 border-none text-gray-400 text-[9px] font-bold uppercase tracking-widest px-2 py-0">
                               {p.status}
                            </Badge>
                            <span className="text-[10px] text-gray-600 font-mono">#{p.id.padStart(3, '0')}</span>
                         </div>

                         <div className="space-y-4 pt-4 border-t border-white/5">
                            <div className="flex items-center justify-between text-[11px] text-gray-500">
                               <div className="flex items-center gap-2">
                                  <FileText className="h-3.5 w-3.5" />
                                  <span>{p.count} Files</span>
                               </div>
                               <div className="flex items-center gap-2">
                                  <Clock className="h-3.5 w-3.5" />
                                  <span>{p.updated}</span>
                               </div>
                            </div>
                            
                            {/* Progress bar mock for aesthetic */}
                            <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                               <div className={`h-full ${p.color} opacity-60`} style={{ width: `${30 + (i * 15)}%` }}></div>
                            </div>
                         </div>
                      </CardContent>
                   </Card>
                </Link>
             ))}
             
             {/* New Project Placeholder */}
             <button className="border border-dashed border-white/10 rounded-2xl flex flex-col items-center justify-center p-8 text-gray-500 hover:text-blue-400 hover:border-blue-500/40 hover:bg-blue-500/5 transition-all group h-full min-h-[260px] relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none"></div>
                <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-all duration-500 shadow-xl group-hover:shadow-blue-500/10 border border-white/5 group-hover:border-blue-500/20">
                   <Plus className="h-8 w-8" />
                </div>
                <div className="font-bold text-sm tracking-wide uppercase">New Workspace</div>
                <div className="text-[10px] text-gray-600 mt-2 font-mono">CTRL + N</div>
             </button>
          </div>
       </div>

       {/* Project Analytics Footer */}
       <div className="mt-auto border-t border-white/5 px-8 py-4 bg-white/5 flex justify-between items-center text-[10px] text-gray-600 font-mono">
          <div className="flex gap-6">
             <div className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-blue-500"></div>
                TOTAL_ASSETS: 1.2k
             </div>
             <div className="flex items-center gap-2">
                <div className="h-1.5 w-1.5 rounded-full bg-green-500"></div>
                HEALTH: OPTIMAL
             </div>
          </div>
          <div className="flex gap-4">
             <span>LATEST_SYNC: {new Date().toLocaleTimeString()}</span>
             <span>REGION: US-EAST-1</span>
          </div>
       </div>
    </div>
  );
}

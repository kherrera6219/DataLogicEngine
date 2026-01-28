'use client';

import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardFooter } from "@/components/ui/card";
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
    <div className="flex h-screen bg-[#111111] text-white font-sans overflow-hidden">
      
      {/* Global Sidebar should be here if layout.tsx handled it, but adding for completeness if standalone */}
      {/* <AppSidebar /> assumed present in layout or added here if needed. 
          For now, keeping it consistent with moving towards global layout. 
          If not global yet, I should add it. I will import it below.
      */}
      
      <div className="flex-1 flex flex-col overflow-y-auto bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">
         
         {/* Acrylic Header */}
         <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center justify-between px-8 backdrop-blur-3xl">
            <div className="flex items-center gap-3">
               <div className="bg-blue-900/10 p-2 rounded-lg border border-blue-500/20">
                  <Folder className="h-5 w-5 text-blue-500" />
               </div>
               <div>
                  <h1 className="text-title font-bold text-gray-100">Projects</h1>
                  <div className="text-[10px] text-gray-500 font-mono">Workspace Manager</div>
               </div>
            </div>
            <Button className="bg-blue-600 hover:bg-blue-700 font-bold shadow-lg shadow-blue-900/20 border-none transition-all hover:scale-105">
               <Plus className="h-4 w-4 mr-2" /> New Project
            </Button>
         </div>

         <div className="max-w-[1600px] w-full mx-auto p-8 space-y-6 animate-connected-enter">
            
            {/* Toolbar */}
            <div className="flex items-center justify-between bg-[#1a1a1a]/50 p-1.5 rounded-xl border border-white/5 backdrop-blur-md">
               <div className="relative w-96">
                  <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
                  <Input placeholder="Search projects..." className="pl-9 bg-black/20 border-transparent hover:bg-black/40 focus:bg-black/50 transition-colors h-9" />
               </div>
               <div className="flex gap-1">
                  <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hover:bg-white/5">
                     <Clock className="h-4 w-4 mr-2" /> Recent
                  </Button>
                  <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hover:bg-white/5">
                     <Star className="h-4 w-4 mr-2" /> Favorites
                  </Button>
                  <div className="w-px h-6 bg-white/10 mx-1 my-auto"></div>
                  <Button variant="ghost" size="sm" className="text-gray-400 hover:text-white hover:bg-white/5">
                     <Filter className="h-4 w-4 mr-2" /> Filter
                  </Button>
               </div>
            </div>

            {/* Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
               {projects.map((p, i) => (
                  <Link href={`/projects/${p.id}`} key={p.id} className="block group">
                     <Card className="fluent-card bg-[#1a1a1a] border-[#333] hover:border-blue-500/30 h-full transition-all duration-300 hover:-translate-y-1 relative overflow-hidden">
                        {/* Status Line */}
                        <div className={`absolute top-0 left-0 right-0 h-1 ${p.color} opacity-80`}></div>
                        
                        <CardContent className="p-6">
                           <div className="flex justify-between items-start mb-6">
                              <div className={`h-12 w-12 rounded-xl ${p.color} bg-opacity-10 flex items-center justify-center border border-white/5 shadow-inner`}>
                                 <p.icon className={`h-6 w-6 ${p.color.replace('bg-', 'text-').replace('-600', '-400')}`} />
                              </div>
                              <Button variant="ghost" size="icon" className="h-8 w-8 -mr-2 text-gray-500 hover:text-white hover:bg-white/5">
                                 <MoreVertical className="h-4 w-4" />
                              </Button>
                           </div>
                           
                           <h3 className="font-semibold text-xl mb-1 text-gray-200 group-hover:text-blue-400 transition-colors tracking-tight">{p.title}</h3>
                           <div className="flex items-center gap-2 mb-4">
                              <Badge variant="outline" className="bg-white/5 border-white/10 text-gray-400 text-[10px] uppercase tracking-wider">
                                 {p.status}
                              </Badge>
                              <span className="text-xs text-gray-600 font-mono">ID-{p.id.padStart(3, '0')}</span>
                           </div>

                           <div className="space-y-3 pt-4 border-t border-white/5">
                              <div className="flex items-center justify-between text-xs text-gray-400">
                                 <div className="flex items-center gap-2">
                                    <FileText className="h-3.5 w-3.5" />
                                    <span>{p.count} Files</span>
                                 </div>
                                 <div className="flex items-center gap-2">
                                    <Clock className="h-3.5 w-3.5" />
                                    <span>{p.updated}</span>
                                 </div>
                              </div>
                           </div>
                        </CardContent>
                     </Card>
                  </Link>
               ))}
               
               {/* New Project Placeholder */}
               <button className="border border-dashed border-white/10 rounded-xl flex flex-col items-center justify-center p-6 text-gray-500 hover:text-blue-400 hover:border-blue-500/30 hover:bg-blue-500/5 transition-all group h-full min-h-[250px] animate-in fade-in duration-700 relative overflow-hidden">
                  <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform shadow-lg group-hover:shadow-blue-900/20">
                     <Plus className="h-8 w-8" />
                  </div>
                  <div className="font-semibold text-sm tracking-wide">Create New Project</div>
               </button>
            </div>
         </div>
      </div>
    </div>
  );
}

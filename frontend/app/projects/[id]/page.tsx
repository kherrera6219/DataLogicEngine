'use client';

import React from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  ArrowLeft, FileText, Upload, Download, Trash2, 
  MoreHorizontal, Plus, Search, FileCode, FileImage 
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";

export default function ProjectDetailPage({ params }: { params: { id: string } }) {
  const files = [
    { name: 'hipaa_compliance_v1.pdf', size: '2.4 MB', type: 'pdf', updated: '2h ago' },
    { name: 'patient_data_schema.json', size: '14 KB', type: 'code', updated: '1d ago' },
    { name: 'security_audit_log.csv', size: '8.1 MB', type: 'csv', updated: '3d ago' },
    { name: 'architecture_diagram.png', size: '4.2 MB', type: 'image', updated: '5d ago' },
  ];

  return (
    <div className="min-h-screen bg-black text-white font-sans flex flex-col">
       {/* Header */}
       <div className="h-16 border-b border-white/10 bg-gray-900/50 backdrop-blur-md flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
             <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 hover:text-white" onClick={() => window.history.back()}>
                <ArrowLeft className="h-4 w-4" />
             </Button>
             <div>
                <h1 className="text-sm font-bold tracking-wide flex items-center gap-2">
                   HIPAA Compliance Audit 
                   <Badge variant="outline" className="text-[10px] bg-blue-900/10 text-blue-400 border-blue-500/30">Active</Badge>
                </h1>
                <div className="text-[10px] text-gray-400 font-mono">ID: {params.id} • Last synced 2m ago</div>
             </div>
          </div>
          <div className="flex gap-2">
             <Button variant="outline" size="sm" className="h-8 border-white/10 text-gray-400 hover:text-white gap-2">
                <Upload className="h-3 w-3" /> Upload Files
             </Button>
             <Button size="sm" className="h-8 bg-blue-600 hover:bg-blue-700 font-bold gap-2">
                <Plus className="h-3 w-3" /> New Note
             </Button>
          </div>
       </div>

       <div className="flex-1 flex">
          {/* Main File Area */}
          <div className="flex-1 p-6">
             
             {/* Toolbar */}
             <div className="flex items-center justify-between mb-6">
                <div className="relative w-64">
                   <Search className="absolute left-2 top-2.5 h-3 w-3 text-gray-500" />
                   <Input placeholder="Filter files..." className="pl-8 bg-white/5 border-white/10 h-8 text-xs" />
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-400">
                   <span>{files.length} items</span>
                   <Separator orientation="vertical" className="h-4" />
                   <span>14.8 MB total</span>
                </div>
             </div>

             {/* File List */}
             <div className="border border-white/10 rounded-lg overflow-hidden bg-gray-900/20">
                <table className="w-full text-left text-xs">
                   <thead className="bg-white/5 text-gray-400 font-mono uppercase">
                      <tr>
                         <th className="p-3 font-medium w-8"></th>
                         <th className="p-3 font-medium">Name</th>
                         <th className="p-3 font-medium">Size</th>
                         <th className="p-3 font-medium">Updated</th>
                         <th className="p-3 font-medium text-right">Actions</th>
                      </tr>
                   </thead>
                   <tbody className="divide-y divide-white/5">
                      {files.map((f, i) => (
                         <tr key={i} className="hover:bg-white/5 transition-colors group cursor-pointer">
                            <td className="p-3 text-center">
                               {f.type === 'pdf' && <FileText className="h-4 w-4 text-red-400" />}
                               {f.type === 'code' && <FileCode className="h-4 w-4 text-yellow-400" />}
                               {f.type === 'image' && <FileImage className="h-4 w-4 text-purple-400" />}
                               {f.type === 'csv' && <FileText className="h-4 w-4 text-green-400" />}
                            </td>
                            <td className="p-3 font-medium text-gray-200 group-hover:text-blue-400">{f.name}</td>
                            <td className="p-3 text-gray-500 font-mono">{f.size}</td>
                            <td className="p-3 text-gray-500">{f.updated}</td>
                            <td className="p-3 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                               <div className="flex justify-end gap-1">
                                  <Button variant="ghost" size="icon" className="h-6 w-6 hover:bg-white/10 text-gray-400 hover:text-white">
                                     <Download className="h-3 w-3" />
                                  </Button>
                                  <Button variant="ghost" size="icon" className="h-6 w-6 hover:bg-red-900/30 text-gray-400 hover:text-red-400">
                                     <Trash2 className="h-3 w-3" />
                                  </Button>
                                  <Button variant="ghost" size="icon" className="h-6 w-6 hover:bg-white/10 text-gray-400 hover:text-white">
                                     <MoreHorizontal className="h-3 w-3" />
                                  </Button>
                               </div>
                            </td>
                         </tr>
                      ))}
                   </tbody>
                </table>
             </div>

             {/* Upload Drop Zone */}
             <div className="mt-6 border-2 border-dashed border-white/10 rounded-xl p-8 flex flex-col items-center justify-center bg-white/[0.02] hover:bg-white/[0.05] transition-colors cursor-pointer text-gray-500">
                <Upload className="h-8 w-8 mb-3 opacity-50" />
                <p className="text-sm font-bold">Drag & Drop files here</p>
                <p className="text-xs mt-1">or click to browse</p>
             </div>
          </div>

          {/* Details Sidebar */}
          <div className="w-80 border-l border-white/10 bg-gray-900/30 p-6">
             <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4">Project Stats</h3>
             <div className="space-y-4">
                <div className="p-4 bg-white/5 rounded-lg border border-white/5">
                   <div className="text-2xl font-bold font-mono text-white">84%</div>
                   <div className="text-xs text-gray-400 mt-1">Compliance Score</div>
                   <div className="w-full bg-gray-700 h-1 mt-2 rounded-full overflow-hidden">
                      <div className="bg-green-500 h-full w-[84%]"></div>
                   </div>
                </div>
                
                <div className="space-y-2">
                   <div className="flex justify-between text-xs text-gray-400">
                      <span>Created</span>
                      <span className="text-white">Jan 12, 2026</span>
                   </div>
                   <div className="flex justify-between text-xs text-gray-400">
                      <span>Owner</span>
                      <span className="text-white">Sarah Connor</span>
                   </div>
                   <div className="flex justify-between text-xs text-gray-400">
                      <span>Access</span>
                      <span className="text-white">Private (Team)</span>
                   </div>
                </div>
             </div>
          </div>
       </div>
    </div>
  );
}

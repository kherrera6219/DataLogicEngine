'use client';

import { Search, Settings, User, Bell, LayoutGrid, Download, HelpCircle, ChevronRight } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";

export function CommandBar() {
  return (
    <div className="w-full h-14 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-4 z-50">
      <div className="flex items-center gap-4">
        <div className="p-2 hover:bg-gray-800 rounded-lg cursor-pointer">
          <LayoutGrid className="h-5 w-5 text-gray-400" />
        </div>
        <div className="h-6 w-px bg-gray-800" />
        <h2 className="text-sm font-bold text-white tracking-tight flex items-center gap-2">
          Knowledge <span className="text-blue-500 underline underline-offset-4 decoration-2">Graph</span> Explorer
        </h2>
        <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[10px] px-1.5 font-bold">
           PROD
        </Badge>
      </div>

      <div className="flex-1 max-w-md mx-8 hidden md:block">
        <div className="relative group">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500 group-focus-within:text-blue-500" />
          <Input 
            className="w-full bg-gray-800/50 border-gray-700/50 h-9 pl-10 focus-visible:ring-blue-500 transition-all rounded-xl" 
            placeholder="Search nodes, pillars, or compliance controls..." 
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex gap-1 mr-2 px-2 py-1 bg-gray-800/50 rounded-lg border border-gray-700/50 hidden lg:flex">
          <Button variant="ghost" size="sm" className="h-7 text-xs text-gray-400 hover:text-white">
            <Download className="h-3.5 w-3.5 mr-1" /> Open in Excel
          </Button>
          <div className="w-px h-4 bg-gray-700 my-auto mx-1" />
          <Button variant="ghost" size="sm" className="h-7 text-xs text-gray-400 hover:text-white">
            Export BI
          </Button>
        </div>

        <div className="flex gap-1">
          {[HelpCircle, Bell, Settings].map((Icon, idx) => (
             <Button key={idx} variant="ghost" size="icon" className="h-9 w-9 text-gray-400 hover:text-white hover:bg-gray-800 rounded-xl">
               <Icon className="h-5 w-5" />
             </Button>
          ))}
          <div className="h-9 w-9 rounded-xl bg-blue-600 flex items-center justify-center text-white text-xs font-bold cursor-pointer">
             AD
          </div>
        </div>
      </div>
    </div>
  );
}

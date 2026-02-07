'use client';

import React from 'react';
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { 
  Settings, Zap, Layers, Users, 
  Lock, Globe, Calendar, GitBranch
} from "lucide-react";
import { 
    Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger 
} from "@/components/ui/sheet";

export function AdvancedControls() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white">
            <Settings className="h-4 w-4" />
        </Button>
      </SheetTrigger>
      <SheetContent side="right" className="bg-white dark:bg-gray-900 border-l border-slate-200 dark:border-white/10 text-gray-900 dark:text-white w-[400px]">
        <SheetHeader>
          <SheetTitle className="text-slate-900 dark:text-white flex items-center gap-2">
            <Settings className="h-4 w-4" /> Advanced Configuration
          </SheetTitle>
          <SheetDescription className="text-slate-600 dark:text-gray-400">
            Fine-tune the AI reasoning engine and validation layers.
          </SheetDescription>
        </SheetHeader>
        
        <div className="py-6 space-y-8">
            
            {/* ⚡ Enhancement Level */}
            <div className="space-y-4">
                <h3 className="text-xs font-bold text-slate-500 dark:text-gray-500 uppercase tracking-wider flex items-center gap-2">
                    <Zap className="h-3 w-3" /> Enhancement Level
                </h3>
                <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 rounded border border-slate-200 dark:border-white/10 bg-white/70 dark:bg-white/5">
                        <div>
                            <div className="text-sm font-bold text-blue-400">High-Stakes</div>
                            <div className="text-[10px] text-slate-600 dark:text-gray-400">99.5% confidence • &lt;15s latency</div>
                        </div>
                        <Badge className="bg-blue-600">Active</Badge>
                    </div>
                    <div className="pt-2">
                        <label className="text-xs text-slate-600 dark:text-gray-400 mb-2 block">Confidence Threshold</label>
                        <Slider defaultValue={[99.5]} max={100} step={0.1} className="w-full" />
                    </div>
                </div>
            </div>

            {/* 🎭 Persona Configuration */}
            <div className="space-y-4">
                <h3 className="text-xs font-bold text-slate-500 dark:text-gray-500 uppercase tracking-wider flex items-center gap-2">
                    <Users className="h-3 w-3" /> Persona Weights
                </h3>
                <div className="space-y-3">
                    {[
                        { name: "Knowledge Expert", color: "bg-blue-500" },
                        { name: "Sector Specialist", color: "bg-orange-500" },
                        { name: "Regulatory Advisor", color: "bg-purple-500" },
                        { name: "Compliance Officer", color: "bg-green-500" }
                    ].map(p => (
                        <div key={p.name} className="space-y-1">
                            <div className="flex justify-between text-xs">
                                <span>{p.name}</span>
                                <span className="text-slate-600 dark:text-gray-400">25%</span>
                            </div>
                            <div className="h-1 bg-slate-300 dark:bg-gray-800 rounded overflow-hidden">
                                <div className={`h-full ${p.color} w-1/4`}></div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

             {/* 🔬 Simulation Layers */}
             <div className="space-y-4">
                <h3 className="text-xs font-bold text-slate-500 dark:text-gray-500 uppercase tracking-wider flex items-center gap-2">
                    <Layers className="h-3 w-3" /> Simulation Layers
                </h3>
                <div className="grid grid-cols-2 gap-2">
                    {['Context Loading', 'Multi-Perspective', 'Deep Research', 'Cross-Axis Valid', 'Neural Analysis', 'Compliance Check'].map(layer => (
                        <div key={layer} className="flex items-center gap-2 text-xs text-slate-700 dark:text-gray-300">
                             <Switch checked={true} className="h-4 w-7" />
                             {layer}
                        </div>
                    ))}
                </div>
            </div>

            {/* 🌐 Context Settings */}
            <div className="space-y-4">
                <h3 className="text-xs font-bold text-slate-500 dark:text-gray-500 uppercase tracking-wider flex items-center gap-2">
                    <Globe className="h-3 w-3" /> Context Context
                </h3>
                <div className="grid grid-cols-2 gap-3">
                    <Button variant="outline" size="sm" className="justify-start text-xs border-slate-300/70 dark:border-white/10 h-8">
                        <Globe className="mr-2 h-3 w-3 text-slate-500 dark:text-gray-500" /> US - California
                    </Button>
                    <Button variant="outline" size="sm" className="justify-start text-xs border-slate-300/70 dark:border-white/10 h-8">
                        <Calendar className="mr-2 h-3 w-3 text-slate-500 dark:text-gray-500" /> Current (2026)
                    </Button>
                    <Button variant="outline" size="sm" className="justify-start text-xs border-slate-300/70 dark:border-white/10 h-8">
                        <Lock className="mr-2 h-3 w-3 text-slate-500 dark:text-gray-500" /> SOC2 + HIPAA
                    </Button>
                    <Button variant="outline" size="sm" className="justify-start text-xs border-slate-300/70 dark:border-white/10 h-8">
                        <GitBranch className="mr-2 h-3 w-3 text-slate-500 dark:text-gray-500" /> Production
                    </Button>
                </div>
            </div>

            <div className="pt-4 border-t border-slate-200 dark:border-white/10 flex gap-2">
                <Button className="flex-1 bg-blue-600 text-white hover:bg-blue-700">Save Preset</Button>
                <Button variant="outline" className="border-slate-300/70 dark:border-white/10 text-slate-700 dark:text-gray-400">Reset</Button>
            </div>

        </div>
      </SheetContent>
    </Sheet>
  );
}

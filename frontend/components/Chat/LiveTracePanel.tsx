import React, { useState, useEffect } from 'react';
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  Activity, Zap, Clock, ShieldCheck, Database, 
  Users, Layers, Terminal, ChevronRight 
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export function LiveTracePanel() {
  const [progress, setProgress] = useState(68);
  const [currentStep, setCurrentStep] = useState('Neural Analysis');
  
  // Simulate live progress
  useEffect(() => {
    const timer = setInterval(() => {
      setProgress(prev => (prev >= 100 ? 0 : prev + 1));
    }, 100);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="h-full flex flex-col bg-gray-900/50 text-white font-sans overflow-hidden">
       {/* Header */}
       <div className="p-4 border-b border-white/10 flex items-center justify-between">
          <h2 className="text-sm font-bold flex items-center gap-2">
             <Activity className="h-4 w-4 text-green-500" />
             Live Trace
          </h2>
          <Badge variant="outline" className="bg-green-900/20 text-green-400 border-green-500/30 text-[10px] px-1.5 py-0 h-5">
             ACTIVE
          </Badge>
       </div>

       <div className="flex-1 overflow-y-auto p-4 space-y-6">
          
          {/* Active Query Status */}
          <div className="space-y-2">
             <div className="text-xs text-gray-500 font-mono uppercase tracking-wider">Active Query</div>
             <div className="p-3 bg-black/40 border border-white/10 rounded-md">
                <div className="flex items-center gap-2 mb-2">
                   <div className="h-1.5 w-1.5 rounded-full bg-yellow-500 animate-pulse"></div>
                   <span className="text-xs text-yellow-500 font-bold">Processing...</span>
                </div>
                <p className="text-xs text-gray-300 italic line-clamp-2">
                   &quot;What are the HIPAA compliance requirements for storing patient data...&quot;
                </p>
             </div>
          </div>

          {/* Current Step */}
          <div className="space-y-2">
             <div className="flex justify-between items-end">
                <div className="text-xs text-gray-500 font-mono uppercase tracking-wider">Current Step</div>
                <div className="text-xs font-mono text-blue-400">Step 7/12</div>
             </div>
             
             <Card className="bg-blue-900/10 border-blue-500/20">
                <CardContent className="p-3">
                   <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-bold text-blue-300 flex items-center gap-2">
                         <Zap className="h-3 w-3" /> {currentStep}
                      </span>
                      <span className="text-xs text-blue-400 font-mono">4.2s</span>
                   </div>
                   <Progress value={progress} className="h-1.5 bg-blue-900/30 [&>div]:bg-blue-500" />
                   <div className="flex justify-between mt-1 text-[10px] text-gray-500">
                      <span>0s</span>
                      <span>15s max</span>
                   </div>
                </CardContent>
             </Card>
          </div>

          {/* Confidence Score */}
          <div className="space-y-2">
             <div className="text-xs text-gray-500 font-mono uppercase tracking-wider">Confidence</div>
             <div className="flex items-center gap-3">
                <div className="flex-1 h-8 bg-black/40 border border-white/10 rounded overflow-hidden relative">
                   <div className="absolute top-0 left-0 h-full bg-green-600/50 w-[94%] border-r border-green-500"></div>
                   <div className="absolute inset-0 flex items-center justify-center text-xs font-bold z-10">
                      94.2%
                   </div>
                </div>
                <div className="text-[10px] text-gray-400">
                   Target: <span className="text-white">99.5%</span>
                </div>
             </div>
          </div>

          {/* Trace Log (Mini) */}
          <div className="space-y-2">
             <div className="text-xs text-gray-500 font-mono uppercase tracking-wider">Trace Log</div>
             <div className="space-y-1">
                {[
                   { name: 'TruthGate Security', time: '100ms', status: 'done' },
                   { name: 'Coord Resolution', time: '300ms', status: 'done' },
                   { name: 'Quad Persona', time: '1.4s', status: 'done' },
                   { name: '12-Step Refine', time: '1.9s', status: 'active' },
                ].map((step, i) => (
                   <div key={i} className="flex items-center justify-between text-xs p-1.5 rounded hover:bg-white/5 transition-colors cursor-pointer group">
                      <div className="flex items-center gap-2">
                         {step.status === 'done' ? (
                            <ShieldCheck className="h-3 w-3 text-green-500" />
                         ) : (
                            <Clock className="h-3 w-3 text-yellow-500 animate-pulse" />
                         )}
                         <span className={step.status === 'active' ? 'text-white font-medium' : 'text-gray-400 group-hover:text-gray-300'}>
                            {step.name}
                         </span>
                      </div>
                      <span className="text-[10px] text-gray-600 font-mono group-hover:text-gray-500">{step.time}</span>
                   </div>
                ))}
             </div>
             <Button variant="ghost" size="sm" className="w-full text-xs text-blue-400 hover:text-blue-300 h-6">
                View Full Tree <ChevronRight className="ml-1 h-3 w-3" />
             </Button>
          </div>

          {/* Quick Stats */}
          <div className="space-y-2 pt-2 border-t border-white/10">
             <div className="text-xs text-gray-500 font-mono uppercase tracking-wider mb-3">Quick Stats</div>
             <div className="grid grid-cols-2 gap-2">
                <div className="p-2 bg-white/5 rounded border border-white/5 flex flex-col items-center justify-center gap-1">
                   <Database className="h-3 w-3 text-purple-400" />
                   <span className="text-lg font-bold">23</span>
                   <span className="text-[9px] text-gray-500 uppercase">Sources</span>
                </div>
                <div className="p-2 bg-white/5 rounded border border-white/5 flex flex-col items-center justify-center gap-1">
                   <Users className="h-3 w-3 text-orange-400" />
                   <span className="text-lg font-bold">4</span>
                   <span className="text-[9px] text-gray-500 uppercase">Personas</span>
                </div>
                <div className="p-2 bg-white/5 rounded border border-white/5 flex flex-col items-center justify-center gap-1">
                   <Layers className="h-3 w-3 text-cyan-400" />
                   <span className="text-lg font-bold">10</span>
                   <span className="text-[9px] text-gray-500 uppercase">Layers</span>
                </div>
                <div className="p-2 bg-white/5 rounded border border-white/5 flex flex-col items-center justify-center gap-1">
                   <Terminal className="h-3 w-3 text-gray-400" />
                   <span className="text-lg font-bold">8</span>
                   <span className="text-[9px] text-gray-500 uppercase">K. Algos</span>
                </div>
             </div>
          </div>
          
          <div className="pt-4 space-y-2">
              <Button variant="outline" size="sm" className="w-full border-white/10 hover:bg-white/5 text-xs h-7">
                  📸 Snapshot
              </Button>
              <Button variant="outline" size="sm" className="w-full border-white/10 hover:bg-white/5 text-xs h-7">
                  📋 Copy Trace
              </Button>
          </div>

       </div>
    </div>
  );
}

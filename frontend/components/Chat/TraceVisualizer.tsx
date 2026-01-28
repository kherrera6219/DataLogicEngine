import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  CheckCircle2, Clock, PlayCircle, 
  ZoomIn
} from "lucide-react";
import { TraceStep } from './types';

export function TraceVisualizer() {
  const steps: TraceStep[] = [
    { id: '1', name: 'TruthGate Security', status: 'completed', durationMs: 100, percentage: 100, timestamp: '0.1s' },
    { id: '2', name: 'Coordinate Resolution', status: 'completed', durationMs: 300, percentage: 100, timestamp: '0.4s' },
    { id: '3', name: 'Knowledge Graph Query', status: 'completed', durationMs: 500, percentage: 100, timestamp: '0.9s' },
    { id: '4', name: 'Quad Persona Sim', status: 'completed', durationMs: 1400, percentage: 100, timestamp: '2.3s' },
    { id: '5', name: 'Deep Neural Analysis', status: 'processing', durationMs: 312, percentage: 68, timestamp: 'CURRENT' },
    { id: '6', name: 'Data Validation', status: 'pending', percentage: 0, timestamp: '---' },
    { id: '7', name: 'Compliance Check', status: 'pending', percentage: 0, timestamp: '---' },
    { id: '8', name: 'Self-Critique', status: 'pending', percentage: 0, timestamp: '---' },
    { id: '9', name: 'Iteration Loop', status: 'pending', percentage: 0, timestamp: '---' },
    { id: '10', name: 'Final Synthesis', status: 'pending', percentage: 0, timestamp: '---' },
  ];

  return (
    <Card className="bg-black/40 border-white/10 mt-6">
      <CardHeader className="py-3 border-b border-white/10 flex flex-row items-center justify-between">
         <CardTitle className="text-sm font-bold flex items-center gap-2">
            <ZoomIn className="h-4 w-4 text-blue-400" /> Interactive Trace Explorer
         </CardTitle>
         <div className="flex gap-2">
            <Badge variant="outline" className="text-[10px] bg-white/5 border-white/10 text-gray-400">Tree View</Badge>
            <Badge variant="outline" className="text-[10px] bg-blue-900/20 border-blue-500/30 text-blue-400">Timeline View</Badge>
         </div>
      </CardHeader>
      <CardContent className="p-4 space-y-4">
         
         {/* Timeline Bar */}
         <div className="relative pt-6 pb-2">
            <div className="absolute top-0 left-0 w-full h-1 bg-white/5 top-[18px]"></div>
            <div className="flex justify-between relative z-10">
               {steps.map((step, i) => (
                  <div key={step.id} className="flex flex-col items-center gap-2 group cursor-pointer">
                     <div className={`
                        w-3 h-3 rounded-full border-2 
                        ${step.status === 'completed' ? 'bg-green-500 border-green-500' : 
                          step.status === 'processing' ? 'bg-blue-500 border-blue-500 animate-pulse' : 
                          'bg-black border-gray-600'}
                     `}></div>
                     <span className={`text-[9px] font-mono max-w-[60px] text-center leading-tight ${step.status === 'pending' ? 'text-gray-600' : 'text-gray-300'}`}>
                        {step.name}
                     </span>
                  </div>
               ))}
            </div>
         </div>

         {/* Detailed Step List */}
         <div className="space-y-1 bg-black/20 rounded-lg p-2 max-h-48 overflow-y-auto custom-scrollbar">
            {steps.map((step) => (
               <div key={step.id} className="flex items-center justify-between p-2 rounded hover:bg-white/5 transition-colors group">
                  <div className="flex items-center gap-3">
                     {step.status === 'completed' && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                     {step.status === 'processing' && <PlayCircle className="h-4 w-4 text-blue-500 animate-spin-slow" />}
                     {step.status === 'pending' && <Clock className="h-4 w-4 text-gray-700" />}
                     
                     <div>
                        <div className={`text-xs font-medium ${step.status === 'pending' ? 'text-gray-600' : 'text-gray-200'}`}>
                           {step.name}
                        </div>
                        {step.status === 'processing' && (
                           <div className="w-24 h-1 bg-gray-800 rounded mt-1 overflow-hidden">
                              <div className="h-full bg-blue-500 animate-progress" style={{ width: `${step.percentage}%` }}></div>
                           </div>
                        )}
                     </div>
                  </div>
                  
                  <div className="text-right">
                     <span className={`text-[10px] font-mono block ${step.status === 'processing' ? 'text-blue-400' : 'text-gray-500'}`}>
                        {step.durationMs ? `${step.durationMs}ms` : '---'}
                     </span>
                     {step.details && <span className="text-[9px] text-gray-600">View Details</span>}
                  </div>
               </div>
            ))}
         </div>

      </CardContent>
    </Card>
  );
}

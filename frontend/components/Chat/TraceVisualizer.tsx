import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  CheckCircle2, Clock, PlayCircle, 
  ZoomIn
} from "lucide-react";
import { TracePipeline, TraceStep } from './types';

interface TraceVisualizerProps {
  trace?: TracePipeline | null;
  hasExecutedQuery?: boolean;
}

export function TraceVisualizer({ trace, hasExecutedQuery = false }: TraceVisualizerProps) {
  const steps: TraceStep[] = trace?.steps || [];

  return (
    <Card className="bg-white/80 dark:bg-black/40 border-slate-200 dark:border-white/10 mt-6">
      <CardHeader className="py-3 border-b border-slate-200 dark:border-white/10 flex flex-row items-center justify-between">
         <CardTitle className="text-sm font-bold flex items-center gap-2">
            <ZoomIn className="h-4 w-4 text-blue-400" /> Interactive Trace Explorer
         </CardTitle>
         <div className="flex gap-2">
            <Badge variant="outline" className="text-[10px] bg-white/70 dark:bg-white/5 border-slate-200 dark:border-white/10 text-slate-600 dark:text-gray-400">Tree View</Badge>
            <Badge variant="outline" className="text-[10px] bg-blue-900/20 border-blue-500/30 text-blue-400">Timeline View</Badge>
         </div>
      </CardHeader>
      <CardContent className="p-4 space-y-4">
         {steps.length === 0 && (
            <div className="rounded-lg border border-dashed border-slate-300/80 dark:border-white/10 bg-slate-50/80 dark:bg-black/20 px-4 py-8 text-center text-xs text-slate-500 dark:text-gray-500">
               {hasExecutedQuery
                  ? 'No trace data returned for this query.'
                  : 'Run a query to populate the trace timeline.'}
            </div>
         )}
         
         {/* Timeline Bar */}
         {steps.length > 0 && <div className="relative pt-6 pb-2">
            <div className="absolute top-0 left-0 w-full h-1 bg-slate-200 dark:bg-white/5 top-[18px]"></div>
            <div className="flex justify-between relative z-10">
               {steps.map((step) => (
                  <div key={step.id} className="flex flex-col items-center gap-2 group cursor-pointer">
                     <div className={`
                        w-3 h-3 rounded-full border-2 
                        ${step.status === 'completed' ? 'bg-green-500 border-green-500' : 
                          step.status === 'processing' ? 'bg-blue-500 border-blue-500 animate-pulse' :
                          'bg-white dark:bg-black border-slate-300 dark:border-gray-600'}
                     `}></div>
                     <span className={`text-[9px] font-mono max-w-[60px] text-center leading-tight ${step.status === 'pending' ? 'text-slate-500 dark:text-gray-600' : 'text-slate-700 dark:text-gray-300'}`}>
                        {step.name}
                     </span>
                  </div>
               ))}
            </div>
         </div>}

         {/* Detailed Step List */}
         {steps.length > 0 && <div className="space-y-1 bg-slate-100/70 dark:bg-black/20 rounded-lg p-2 max-h-48 overflow-y-auto custom-scrollbar">
            {steps.map((step) => (
               <div key={step.id} className="flex items-center justify-between p-2 rounded hover:bg-slate-200/70 dark:hover:bg-white/5 transition-colors group">
                  <div className="flex items-center gap-3">
                     {step.status === 'completed' && <CheckCircle2 className="h-4 w-4 text-green-500" />}
                     {step.status === 'processing' && <PlayCircle className="h-4 w-4 text-blue-500 animate-spin-slow" />}
                     {step.status === 'pending' && <Clock className="h-4 w-4 text-slate-500 dark:text-gray-700" />}
                     
                     <div>
                        <div className={`text-xs font-medium ${step.status === 'pending' ? 'text-slate-500 dark:text-gray-600' : 'text-slate-800 dark:text-gray-200'}`}>
                           {step.name}
                        </div>
                        {step.status === 'processing' && (
                           <div className="w-24 h-1 bg-slate-300 dark:bg-gray-800 rounded mt-1 overflow-hidden">
                              <div className="h-full bg-blue-500 animate-progress" style={{ width: `var(--step-progress, ${step.percentage}%)` } as React.CSSProperties}></div>
                           </div>
                        )}
                     </div>
                  </div>
                  
                  <div className="text-right">
                     <span className={`text-[10px] font-mono block ${step.status === 'processing' ? 'text-blue-400' : 'text-slate-500 dark:text-gray-500'}`}>
                        {step.durationMs !== undefined ? `${step.durationMs}ms` : '---'}
                     </span>
                     {step.details && <span className="text-[9px] text-slate-500 dark:text-gray-600">View Details</span>}
                  </div>
               </div>
            ))}
         </div>}

      </CardContent>
    </Card>
  );
}

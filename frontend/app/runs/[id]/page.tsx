'use client';

import { useState, useEffect } from 'react';
import { api, TraceDetail } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function TraceDetailPage({ params }: { params: { id: string } }) {
  const [trace, setTrace] = useState<TraceDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Unwrap params (Next.js 15+ may require await, but Next 14 handles it fine usually. 
  // However, strict types might complain. Treating as simple obj for now.)
  const runId = params.id;

  useEffect(() => {
     let mounted = true;
     if (runId) {
        api.trace.get(runId).then(data => {
           if (mounted) {
              setTrace(data);
              setIsLoading(false);
           }
        });
     }
     return () => { mounted = false; };
  }, [runId]);

  if (isLoading) {
     return <div className="p-8 text-center text-gray-500">Loading trace details...</div>;
  }

  if (!trace) {
     return <div className="p-8 text-center text-red-500">Trace not found</div>;
  }

  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8">
      <div className="container mx-auto max-w-7xl">
         <header className="mb-8 flex justify-between items-center">
            <div>
               <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Trace Detail</h1>
               <div className="flex items-center gap-2 mt-2">
                  <span className="font-mono text-gray-500">{trace.run_id}</span>
                  <Badge variant={trace.status === 'completed' ? 'success' : 'secondary'}>{trace.status}</Badge>
               </div>
            </div>
            <Button variant="outline">Download Logs</Button>
         </header>

         <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
               <Card>
                  <CardHeader>
                     <CardTitle>Evidence Chain</CardTitle>
                     <CardDescription>Reasoning steps and retrieved context.</CardDescription>
                  </CardHeader>
                  <CardContent>
                     {/* If real stages exist, map them. Else show placeholder or empty state */}
                     <div className="space-y-4">
                        {!trace.stages?.length && (
                           <p className="text-gray-500 italic">No detailed stage information available.</p>
                        )}
                        {trace.stages?.map((step: any, i: number) => (
                           <div key={i} className="p-4 bg-white dark:bg-gray-900 border rounded-lg">
                              <div className="flex justify-between mb-2">
                                 <h4 className="font-semibold text-sm">Step {i+1}: {step.name || 'Processing'}</h4>
                                 <span className="text-xs text-gray-500">{step.duration}ms</span>
                              </div>
                              <p className="text-sm text-gray-600 dark:text-gray-300">
                                 {step.description || 'Step execution completed.'}
                              </p>
                           </div>
                        ))}
                     </div>
                  </CardContent>
               </Card>
            </div>

            <div className="space-y-6">
               <Card>
                  <CardHeader>
                     <CardTitle>Metadata</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4 text-sm">
                     <div className="flex justify-between">
                        <span className="text-gray-500">KA ID</span>
                        <span className="font-medium">{trace.ka_id || 'N/A'}</span>
                     </div>
                     <div className="flex justify-between">
                        <span className="text-gray-500">Created</span>
                        <span className="font-medium">{new Date(trace.created_at).toLocaleString()}</span>
                     </div>
                     {trace.scores && (
                        <>
                           <div className="flex justify-between">
                              <span className="text-gray-500">Confidence</span>
                              <span className="font-medium">{(trace.scores.confidence * 100).toFixed(0)}%</span>
                           </div>
                           <div className="flex justify-between">
                              <span className="text-gray-500">Bias Risk</span>
                              <span className="font-medium">{trace.scores.bias_risk.toFixed(2)}</span>
                           </div>
                        </>
                     )}
                  </CardContent>
               </Card>
            </div>
         </div>
      </div>
    </main>
  );
}

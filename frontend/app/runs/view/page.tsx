'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { api, TraceDetail } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TracePersona, TraceAxisVector, TraceStage } from '@/lib/api/types';

function TraceDetailContent() {
  const searchParams = useSearchParams();
  const runId = searchParams.get('id');
  
  const [trace, setTrace] = useState<TraceDetail | null>(null);
  const [personas, setPersonas] = useState<TracePersona[]>([]);
  const [axes, setAxes] = useState<TraceAxisVector | null>(null);
  const [stages, setStages] = useState<TraceStage[]>([]); // Use TraceStage[]
  const [activeTab, setActiveTab] = useState("evidence");
  const [isLoading, setIsLoading] = useState(!!runId);

  useEffect(() => {
     let mounted = true;
     if (runId) {
        Promise.all([
            api.trace.get(runId),
            api.trace.getPersonas(runId).catch(() => ({ personas: [] })),
            api.trace.getAxes(runId).catch(() => ({ axes: null })),
            api.trace.getStages(runId).catch(() => ({ stages: [] }))
        ]).then(([traceData, personaData, axisData, stageData]) => {
           if (mounted) {
              setTrace(traceData as TraceDetail);
              setPersonas((personaData as { personas: TracePersona[] }).personas || []);
              setAxes((axisData as { axes: TraceAxisVector }).axes || null);
              setStages((stageData as { stages: TraceStage[] }).stages || []);
              setIsLoading(false);
           }
        }).catch((err) => {
            console.error(err);
           if (mounted) setIsLoading(false);
        });
     }
     return () => { mounted = false; };
  }, [runId]);

  if (isLoading) {
     return <div className="p-8 text-center text-gray-500">Loading trace details...</div>;
  }

  if (!trace) {
     return <div className="p-8 text-center text-red-500">{runId ? 'Trace not found' : 'No trace ID provided'}</div>;
  }

  return (
      <div className="container mx-auto max-w-7xl space-y-8">
         <header className="flex justify-between items-center">
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
            <div className="lg:col-span-2">
               <Tabs defaultValue="evidence" value={activeTab} onValueChange={setActiveTab}>
                  <TabsList className="grid w-full grid-cols-3">
                     <TabsTrigger value="evidence">Evidence Chain</TabsTrigger>
                     <TabsTrigger value="personas">Expert Analysis</TabsTrigger>
                     <TabsTrigger value="coordinates">Coordinates</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="evidence" className="space-y-4 mt-4">
                     <Card>
                        <CardHeader>
                           <CardTitle>Reasoning Trace</CardTitle>
                           <CardDescription>Layered execution path.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                           {!stages?.length && (
                              <p className="text-gray-500 italic">No detailed stage information available.</p>
                           )}
                           {stages?.map((step, i) => (
                              <div key={i} className="p-4 bg-white dark:bg-gray-900 border rounded-lg relative overflow-hidden">
                                 {/* Layer/Step Indicator */}
                                 {(step.layer_index || step.step_index) && (
                                     <div className="absolute top-0 right-0 px-2 py-1 bg-gray-100 dark:bg-gray-800 text-xs font-mono text-gray-500 rounded-bl-lg">
                                         {step.stage_type === 'layer' ? `L${step.layer_index}` : `S${step.step_index}`}
                                     </div>
                                 )}
                                 
                                 <div className="flex justify-between mb-2">
                                    <h4 className="font-semibold text-sm">{step.algorithm_name || step.name || 'Processing'}</h4>
                                    <span className={`text-xs px-2 py-0.5 rounded-full ${step.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                                        {step.status}
                                    </span>
                                 </div>
                                 <p className="text-sm text-gray-600 dark:text-gray-300">
                                    Started: {new Date(step.started_at || step.start_time!).toLocaleTimeString()}
                                 </p>
                                 {/* Show Inputs/Outputs if available */}
                                 {step.outputs && (
                                     <div className="mt-2 text-xs text-gray-500 font-mono bg-gray-50 dark:bg-gray-950 p-2 rounded">
                                         {JSON.stringify(step.outputs).slice(0, 100)}
                                         {JSON.stringify(step.outputs).length > 100 && '...'}
                                     </div>
                                 )}
                              </div>
                           ))}
                        </CardContent>
                     </Card>
                  </TabsContent>

                  <TabsContent value="personas" className="space-y-4 mt-4">
                     <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {personas.map((p) => (
                           <Card key={p.persona_id} className="border-l-4 border-l-blue-500">
                              <CardHeader className="pb-2">
                                 <CardTitle className="text-lg flex justify-between">
                                    {p.persona_name}
                                    <Badge variant="outline" className="text-xs uppercase">{p.persona_type}</Badge>
                                 </CardTitle>
                              </CardHeader>
                              <CardContent>
                                 <p className="text-sm text-gray-600 dark:text-gray-300 italic mb-3">
                                    &quot;{p.draft?.text?.slice(0, 150)}{p.draft?.text && p.draft.text.length > 150 ? '...' : ''}&quot;
                                 </p>
                                 <div className="flex justify-between items-center text-xs text-gray-500">
                                     <span>Confidence: {(p.confidence || 0) * 100}%</span>
                                     <span className="capitalize">{p.status}</span>
                                 </div>
                              </CardContent>
                           </Card>
                        ))}
                        {!personas.length && (
                            <div className="col-span-2 p-8 text-center text-gray-500 border rounded-lg border-dashed">
                                No persona activation data found for this run.
                            </div>
                        )}
                     </div>
                  </TabsContent>

                  <TabsContent value="coordinates" className="space-y-4 mt-4">
                     <Card>
                        <CardHeader>
                           <CardTitle>17-Axis Vector</CardTitle>
                           <CardDescription>Multidimensional logic coordinates.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            {axes ? (
                                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                                    {Object.entries(axes.axes).map(([id, axis]) => (
                                        <div key={id} className={`p-3 rounded-lg border ${axis.selected ? 'bg-blue-50/50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800' : 'bg-gray-50 border-gray-100 dark:bg-gray-900/50 dark:border-gray-800'}`}>
                                            <div className="text-xs text-gray-500 uppercase font-bold mb-1">Axis {id}</div>
                                            <div className="font-medium text-sm truncate" title={axis.name}>{axis.name}</div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="p-8 text-center text-gray-500 border rounded-lg border-dashed">
                                    No coordinate vector data found for this run.
                                </div>
                            )}
                        </CardContent>
                     </Card>
                  </TabsContent>
               </Tabs>
            </div>

            <div className="space-y-6">
               <Card>
                  <CardHeader>
                     <CardTitle>Metadata</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4 text-sm">
                     <div className="flex justify-between">
                        <span className="text-gray-500">KA ID</span>
                        <span className="font-mono bg-gray-100 px-1 rounded">{trace.ka_id || 'N/A'}</span>
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
  );
}

export default function TraceDetailPage() {
  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8">
      <Suspense fallback={<div className="p-8 text-center text-gray-500">Loading...</div>}>
         <TraceDetailContent />
      </Suspense>
    </main>
  );
}

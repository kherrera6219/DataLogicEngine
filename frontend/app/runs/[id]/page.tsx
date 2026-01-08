'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export default function TraceDetailPage({ params }: { params: { id: string } }) {
  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8">
      <div className="container mx-auto max-w-7xl">
         <header className="mb-8 flex justify-between items-center">
            <div>
               <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Trace Detail</h1>
               <div className="flex items-center gap-2 mt-2">
                  <span className="font-mono text-gray-500">{params.id}</span>
                  <Badge variant="success">Completed</Badge>
               </div>
            </div>
            <Button variant="outline">Download Logs</Button>
         </header>

         <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
               <Card>
                  <CardHeader>
                     <CardTitle>Execution DAG</CardTitle>
                     <CardDescription>Visual representation of reasoning steps.</CardDescription>
                  </CardHeader>
                  <CardContent className="h-64 flex items-center justify-center border-2 border-dashed border-gray-200 rounded-lg bg-gray-50">
                      <span className="text-gray-400">Graph Visualization Placeholder</span>
                  </CardContent>
               </Card>

               <Card>
                  <CardHeader>
                     <CardTitle>Evidence Chain</CardTitle>
                  </CardHeader>
                  <CardContent>
                     <div className="space-y-4">
                        {[1, 2, 3].map((step) => (
                           <div key={step} className="p-4 bg-white dark:bg-gray-900 border rounded-lg">
                              <div className="flex justify-between mb-2">
                                 <h4 className="font-semibold text-sm">Step {step}: Inference</h4>
                                 <span className="text-xs text-gray-500">12ms</span>
                              </div>
                              <p className="text-sm text-gray-600 dark:text-gray-300">
                                 Analyzed node relationship strengths. Found high correlation (0.89) between Input A and Knowledge B.
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
                        <span className="text-gray-500">Algorithm</span>
                        <span className="font-medium">KA-001</span>
                     </div>
                     <div className="flex justify-between">
                        <span className="text-gray-500">Initiator</span>
                        <span className="font-medium">User: Admin</span>
                     </div>
                     <div className="flex justify-between">
                        <span className="text-gray-500">Duration</span>
                        <span className="font-medium">1.24s</span>
                     </div>
                  </CardContent>
               </Card>
            </div>
         </div>
      </div>
    </main>
  );
}

'use client';

import useSWR from 'swr';
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

export default function AnalyticsPage() {
  const { data: pillars, isLoading } = useSWR('knowledge-pillars', () => api.knowledge.pillars());

  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8">
      <div className="container mx-auto max-w-7xl">
         <header className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Analytics</h1>
            <p className="text-gray-500">17-Axis Framework Overview and System Metrics.</p>
         </header>

         {/* 17-Axis Framework Overview */}
         <Card>
             <CardHeader>
                <CardTitle>17-Axis Framework Coverage</CardTitle>
                <CardDescription>Knowledge Graph distribution across dimensional axes.</CardDescription>
             </CardHeader>
             <CardContent>
                {isLoading ? (
                    <div className="space-y-4">
                        <Skeleton className="h-20 w-full" />
                        <Skeleton className="h-20 w-full" />
                        <Skeleton className="h-20 w-full" />
                    </div>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                       <div className="space-y-4">
                          <h4 className="text-sm font-semibold text-gray-500 uppercase">Core (1-5)</h4>
                          <div className="space-y-2">
                             {(pillars || []).filter(p => p.pillar_id >= 1 && p.pillar_id <= 5).map((p) => (
                                <div key={p.uid} className="flex items-center justify-between p-2 bg-gray-100 dark:bg-gray-800 rounded">
                                   <div className="flex items-center gap-2">
                                      <Badge variant="outline" className="w-6 h-6 rounded-full flex items-center justify-center p-0">{p.pillar_id}</Badge>
                                      <span className="text-sm font-medium">{p.name}</span>
                                   </div>
                                   <div className="text-xs text-gray-500">Active</div>
                                </div>
                             ))}
                             {(pillars || []).filter(p => p.pillar_id >= 1 && p.pillar_id <= 5).length === 0 && (
                                 <p className="text-xs text-muted-foreground">No core pillars defined.</p>
                             )}
                          </div>
                       </div>
    
                       <div className="space-y-4">
                          <h4 className="text-sm font-semibold text-gray-500 uppercase">Crosswalk (6-7)</h4>
                          <div className="space-y-2">
                             {/* Mock for now as these might not be in DB yet */}
                             {["Octopus (Reg)", "Spiderweb (Comp)"].map((axis, i) => (
                                <div key={axis} className="flex items-center justify-between p-2 bg-gray-100 dark:bg-gray-800 rounded">
                                   <div className="flex items-center gap-2">
                                      <Badge variant="outline" className="w-6 h-6 rounded-full flex items-center justify-center p-0">{i+6}</Badge>
                                      <span className="text-sm font-medium">{axis}</span>
                                   </div>
                                   <div className="text-xs text-gray-500">12%</div>
                                </div>
                             ))}
                          </div>
                       </div>
    
                       <div className="space-y-4">
                          <h4 className="text-sm font-semibold text-gray-500 uppercase">Personas (8-11)</h4>
                          <div className="space-y-2">
                             {["Knowledge Expert", "Sector Expert", "Regulatory Expert", "Compliance Expert"].map((axis, i) => (
                                <div key={axis} className="flex items-center justify-between p-2 bg-gray-100 dark:bg-gray-800 rounded">
                                   <div className="flex items-center gap-2">
                                      <Badge variant="outline" className="w-6 h-6 rounded-full flex items-center justify-center p-0">{i+8}</Badge>
                                      <span className="text-sm font-medium">{axis}</span>
                                   </div>
                                   <div className="text-xs text-gray-500">45 Active</div>
                                </div>
                             ))}
                          </div>
                       </div>
    
                       <div className="space-y-4">
                          <h4 className="text-sm font-semibold text-gray-500 uppercase">Context (12-13)</h4>
                          <div className="space-y-2">
                             {["Location Context", "Temporal Logic"].map((axis, i) => (
                                <div key={axis} className="flex items-center justify-between p-2 bg-gray-100 dark:bg-gray-800 rounded">
                                   <div className="flex items-center gap-2">
                                      <Badge variant="outline" className="w-6 h-6 rounded-full flex items-center justify-center p-0">{i+12}</Badge>
                                      <span className="text-sm font-medium">{axis}</span>
                                   </div>
                                   <div className="text-xs text-gray-500">Global</div>
                                </div>
                             ))}
                          </div>
                       </div>
    
                       <div className="space-y-4">
                          <h4 className="text-sm font-semibold text-gray-500 uppercase">Enterprise (14-17)</h4>
                          <div className="space-y-2">
                             {["Risk & Conf", "Fed Intel", "Arrows of Time", "Observability"].map((axis, i) => (
                                <div key={axis} className="flex items-center justify-between p-2 bg-gray-100 dark:bg-gray-800 rounded">
                                   <div className="flex items-center gap-2">
                                      <Badge variant="outline" className="w-6 h-6 rounded-full flex items-center justify-center p-0">{i+14}</Badge>
                                      <span className="text-sm font-medium">{axis}</span>
                                   </div>
                                   <div className="text-xs text-gray-500">High</div>
                                </div>
                             ))}
                          </div>
                       </div>
                    </div>
                )}
             </CardContent>
         </Card>
      </div>
    </main>
  );
}

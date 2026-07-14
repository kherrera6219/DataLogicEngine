'use client';

import useSWR from 'swr';
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Database, Layers } from "lucide-react";

export default function KnowledgePage() {
  const { data: pillars, isLoading, error } = useSWR('knowledge-pillars', api.knowledge.pillars);
  const { data: graph, isLoading: graphLoading, error: graphError } = useSWR(
    'knowledge-pillar-counts',
    () => api.knowledge.graph(),
  );

  const nodeCountByPillar = (graph?.nodes || []).reduce<Record<string, number>>((counts, node) => {
    if (node.node_type !== 'pillar' && node.pillar) {
      counts[node.pillar] = (counts[node.pillar] || 0) + 1;
    }
    return counts;
  }, {});

  return (
    <div className="min-h-full bg-background text-foreground font-sans">
      <div className="min-h-full bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">

        {/* Acrylic Header */}
        <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center justify-between px-8 backdrop-blur-3xl">
          <div className="flex items-center gap-3">
            <div className="bg-blue-500/10 p-2 rounded-lg border border-blue-500/20">
              <Database className="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <h1 className="text-title font-bold text-slate-900 dark:text-gray-100">Knowledge Base</h1>
              <div className="text-[10px] text-slate-500 dark:text-gray-500 font-mono uppercase tracking-widest">Universal Knowledge Graph — Pillar View</div>
            </div>
          </div>
        </div>

        <div className="max-w-[1600px] w-full mx-auto p-8 space-y-8 animate-connected-enter">
          <p className="text-slate-500 dark:text-gray-400 max-w-3xl text-sm leading-relaxed">
            The Universal Knowledge Graph is organized into hierarchical pillars.
            Counts and states below reflect the graph records currently available to this application.
          </p>

          {error && (
            <Card className="border-red-500/30 bg-red-500/10" role="alert">
              <CardContent className="p-4 text-sm text-red-600 dark:text-red-300">
                {error instanceof Error ? error.message : 'Failed to load the Knowledge Graph pillars.'}
              </CardContent>
            </Card>
          )}

          {graphError && (
            <Card className="border-amber-500/30 bg-amber-500/10" role="status">
              <CardContent className="p-4 text-sm text-amber-700 dark:text-amber-300">
                Pillar definitions are available, but live graph counts could not be loaded.
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {isLoading && Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} className="fluent-card border-l-4 border-l-transparent">
                <CardHeader>
                  <div className="flex justify-between">
                    <Skeleton className="h-6 w-32" />
                    <Skeleton className="h-5 w-16" />
                  </div>
                  <Skeleton className="h-4 w-full mt-2" />
                </CardHeader>
                <CardContent>
                  <div className="flex justify-between items-end mt-4">
                    <div className="space-y-2">
                      <Skeleton className="h-8 w-12" />
                      <Skeleton className="h-3 w-8" />
                    </div>
                    <Skeleton className="h-12 w-12 rounded-full" />
                  </div>
                </CardContent>
              </Card>
            ))}

            {!isLoading && pillars?.length === 0 && (
              <Card className="col-span-full fluent-card border-dashed p-8 text-center flex flex-col items-center justify-center text-slate-500 dark:text-muted-foreground space-y-4">
                <Database className="h-12 w-12 opacity-20" />
                <p>No pillars defined in the Knowledge Graph yet.</p>
                <p className="text-sm">Run the initialization pipeline to seed core data.</p>
              </Card>
            )}

            {pillars?.map((pillar) => (
              <Card key={pillar.uid} className="fluent-card hover:-translate-y-1 cursor-pointer border-l-4 border-l-blue-500/30 hover:border-l-blue-500 group">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-xl text-slate-900 dark:text-gray-100 group-hover:text-blue-400 transition-colors">{pillar.name}</CardTitle>
                    <Badge variant="outline" className="bg-green-500/10 text-green-400 border-green-500/20 text-[10px] font-bold uppercase">
                      Defined
                    </Badge>
                  </div>
                  <CardDescription className="text-slate-500 dark:text-gray-500">{pillar.description || 'Core knowledge pillar.'}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex justify-between items-end mt-4">
                    <div>
                      <div className="text-3xl font-bold tracking-tighter text-slate-900 dark:text-gray-100">
                        {graphLoading ? '…' : graphError ? 'Unavailable' : (nodeCountByPillar[pillar.name] || 0)}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-muted-foreground uppercase font-medium mt-1 tracking-wider">
                        {graphError ? 'Graph state' : 'Visible nodes'}
                      </div>
                    </div>
                    <div className="w-12 h-12 bg-blue-500/10 rounded-full flex items-center justify-center text-blue-400 group-hover:scale-110 transition-transform border border-blue-500/20">
                      <Layers className="h-6 w-6" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

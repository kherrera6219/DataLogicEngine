'use client';

import useSWR from 'swr';
import { api } from "@/lib/api";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { BookOpen, Database, Layers } from "lucide-react";

export default function KnowledgePage() {
  const { data: pillars, isLoading } = useSWR('knowledge-pillars', api.knowledge.pillars);

  return (
    <main className="min-h-screen bg-muted/40 p-8">
      <div className="container mx-auto max-w-7xl space-y-8">
        <header>
          <h1 className="text-3xl font-bold tracking-tight mb-2">Knowledge Base</h1>
          <p className="text-muted-foreground max-w-3xl">
            The Universal Knowledge Graph is organized into hierarchical pillars. 
            Each pillar contains interconnected domain nodes verified by the Truth Engine.
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {isLoading && Array.from({ length: 6 }).map((_, i) => (
              <Card key={i} className="border-l-4 border-l-transparent">
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
              <Card className="col-span-full border-dashed p-8 text-center flex flex-col items-center justify-center text-muted-foreground space-y-4">
                  <Database className="h-12 w-12 opacity-20" />
                  <p>No pillars defined in the Knowledge Graph yet.</p>
                  <p className="text-sm">Run the initialization pipeline to seed core data.</p>
              </Card>
          )}

          {pillars?.map((pillar) => (
            <Card key={pillar.uid} className="hover:shadow-md transition-shadow cursor-pointer border-l-4 border-l-primary/40 hover:border-l-primary group">
              <CardHeader>
                <div className="flex justify-between items-start">
                   <CardTitle className="text-xl group-hover:text-primary transition-colors">{pillar.name}</CardTitle>
                   <Badge variant="outline">
                      Active
                   </Badge>
                </div>
                <CardDescription>{pillar.description || 'Core knowledge pillar.'}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between items-end mt-4">
                  <div>
                    <div className="text-3xl font-bold tracking-tighter">
                       {/* Placeholder count until real node count API exists per pillar */}
                       -- 
                    </div>
                    <div className="text-xs text-muted-foreground uppercase font-medium mt-1">Nodes</div>
                  </div>
                  <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center text-primary group-hover:scale-110 transition-transform">
                     <Layers className="h-6 w-6" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </main>
  );
}

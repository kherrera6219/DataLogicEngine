'use client';

import Link from 'next/link';
import { Database, Network } from 'lucide-react';
import KnowledgeIngestionSettings from '@/components/settings/KnowledgeIngestionSettings';
import { Card, CardContent } from '@/components/ui/card';

export default function KnowledgePage() {
  return (
    <div className="min-h-full bg-background text-foreground">
      <header className="sticky top-0 z-10 flex min-h-16 items-center border-b border-white/5 px-4 backdrop-blur-3xl sm:px-8">
        <div className="flex items-center gap-3">
          <div className="rounded-lg border border-blue-500/20 bg-blue-500/10 p-2">
            <Database className="h-5 w-5 text-blue-500" aria-hidden="true" />
          </div>
          <div>
            <h1 className="text-title font-bold">Knowledge Base</h1>
            <p className="text-xs text-slate-500">Source, revision, materialization, and retrieval authority</p>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-[1600px] space-y-6 p-4 sm:p-8">
        <Card className="fluent-card">
          <CardContent className="flex flex-col gap-4 p-5 md:flex-row md:items-center md:justify-between">
            <div className="max-w-3xl">
              <h2 className="font-semibold">Authoritative knowledge workspace</h2>
              <p className="mt-1 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
                Manage local sources and inspect source revisions, materialization, and retrieval status. File details are content-free and limited to the owning principal. Relationship browsing remains in the graph workspace.
              </p>
            </div>
            <Link
              href="/graph"
              className="inline-flex min-h-10 shrink-0 items-center justify-center gap-2 rounded-lg border border-blue-500/30 px-4 text-sm font-medium text-blue-700 hover:bg-blue-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:text-blue-300"
            >
              <Network className="h-4 w-4" aria-hidden="true" />
              Browse relationships
            </Link>
          </CardContent>
        </Card>

        <KnowledgeIngestionSettings />
      </main>
    </div>
  );
}

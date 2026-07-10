'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { request } from '@/lib/api';
import { Cpu, Search } from 'lucide-react';

interface AlgorithmRecord {
  id: string;
  name: string;
  category?: string;
  purpose?: string;
  description?: string;
  notes?: string;
  risk_class?: string;
  status?: string;
}

interface AlgorithmListResponse {
  algorithms?: AlgorithmRecord[];
  total_count?: number;
}

function algorithmDescription(entry: AlgorithmRecord): string {
  return (
    entry.purpose?.trim() ||
    entry.description?.trim() ||
    entry.notes?.trim() ||
    'No algorithm description is available.'
  );
}
export default function AlgorithmsPage() {
  const [algorithms, setAlgorithms] = useState<AlgorithmRecord[]>([]);
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadAlgorithms() {
      setError(null);
      try {
        const response = await request<AlgorithmListResponse>('/ka/algorithms?per_page=300');
        if (!cancelled) {
          setAlgorithms(response.algorithms || []);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load algorithm registry');
          setAlgorithms([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    void loadAlgorithms();
    return () => {
      cancelled = true;
    };
  }, []);

  const filteredAlgorithms = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return algorithms;
    return algorithms.filter((entry) =>
      `${entry.id} ${entry.name} ${entry.category || ''} ${algorithmDescription(entry)}`.toLowerCase().includes(needle)
    );
  }, [algorithms, query]);

  return (
    <div className="min-h-full bg-background text-foreground font-sans">
      <div className="min-h-full bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">

        {/* Acrylic Header */}
        <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center justify-between px-8 backdrop-blur-3xl">
          <div className="flex items-center gap-3">
            <div className="bg-amber-500/10 p-2 rounded-lg border border-amber-500/20">
              <Cpu className="h-5 w-5 text-amber-400" />
            </div>
            <div>
              <h1 className="text-title font-bold text-slate-900 dark:text-gray-100">Algorithm Registry</h1>
              <div className="text-[10px] text-slate-500 dark:text-gray-500 font-mono uppercase tracking-widest">Live catalog from /api/v1/ka/algorithms</div>
            </div>
          </div>
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 dark:text-gray-500" aria-hidden="true" />
            <Input
              aria-label="Search algorithms"
              placeholder="Search algorithms..."
              className="pl-9 h-9 bg-white/70 dark:bg-black/20 border-slate-200 dark:border-white/10 text-sm"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>
        </div>

        <div className="max-w-[1600px] w-full mx-auto p-8 space-y-8 animate-connected-enter">

          {error && (
            <Card className="border-red-500/30 bg-red-500/10">
              <CardContent className="p-4 text-sm text-red-600 dark:text-red-300">
                {error}
              </CardContent>
            </Card>
          )}

          {loading && (
            <Card className="fluent-card">
              <CardContent className="p-6 text-sm text-muted-foreground">
                Loading algorithm registry...
              </CardContent>
            </Card>
          )}

          {!loading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredAlgorithms.map((entry) => (
                <Card key={entry.id} className="fluent-card hover:-translate-y-1 cursor-pointer group">
                  <CardHeader>
                    <div className="flex justify-between items-start mb-2">
                      <Badge variant="outline" className="font-mono text-xs bg-white/70 dark:bg-white/5 border-slate-200 dark:border-white/10">{entry.id}</Badge>
                      <Badge variant="secondary" className="bg-amber-500/10 text-amber-400 border-amber-500/20 text-[10px] font-bold uppercase">{entry.risk_class || entry.status || 'Unknown'}</Badge>
                    </div>
                    <CardTitle className="text-lg text-slate-900 dark:text-gray-100 group-hover:text-blue-400 transition-colors">{entry.name}</CardTitle>
                    <CardDescription className="text-slate-500 dark:text-gray-500">{entry.category || 'Uncategorized'}</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-slate-600 dark:text-gray-400">
                      {algorithmDescription(entry)}
                    </p>
                  </CardContent>
                </Card>
              ))}
              {!error && filteredAlgorithms.length === 0 && (
                <Card className="col-span-full fluent-card flex items-center justify-center p-8 border-dashed">
                  <p className="text-slate-500 dark:text-gray-400 text-sm text-center">
                    No algorithms matched your filters.
                  </p>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

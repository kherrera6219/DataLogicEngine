'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { request } from '@/lib/api';

interface AlgorithmRecord {
  id: string;
  name: string;
  category?: string;
  purpose?: string;
  risk_class?: string;
  status?: string;
}

interface AlgorithmListResponse {
  algorithms?: AlgorithmRecord[];
  total_count?: number;
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
      `${entry.id} ${entry.name} ${entry.category || ''} ${entry.purpose || ''}`.toLowerCase().includes(needle)
    );
  }, [algorithms, query]);

  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8">
      <div className="container mx-auto max-w-7xl">
        <header className="mb-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Algorithm Registry</h1>
            <p className="text-gray-500">Live catalog loaded from `/api/v1/ka/algorithms`.</p>
          </div>
          <div className="flex w-full md:w-auto gap-2">
            <Input
              placeholder="Search algorithms..."
              className="w-full md:w-64"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
            <Button type="button">Search</Button>
          </div>
        </header>

        {error && (
          <Card className="mb-6 border-red-500/30 bg-red-500/10">
            <CardContent className="p-4 text-sm text-red-600 dark:text-red-300">
              {error}
            </CardContent>
          </Card>
        )}

        {loading && (
          <Card>
            <CardContent className="p-6 text-sm text-muted-foreground">
              Loading algorithm registry...
            </CardContent>
          </Card>
        )}

        {!loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredAlgorithms.map((entry) => (
              <Card key={entry.id} className="hover:border-blue-500 transition-colors cursor-pointer group">
                <CardHeader>
                  <div className="flex justify-between items-start mb-2">
                    <Badge variant="outline" className="font-mono text-xs">{entry.id}</Badge>
                    <Badge variant="secondary">{entry.risk_class || entry.status || 'Unknown'}</Badge>
                  </div>
                  <CardTitle className="text-lg group-hover:text-blue-600 transition-colors">{entry.name}</CardTitle>
                  <CardDescription>{entry.category || 'Uncategorized'}</CardDescription>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 dark:text-gray-300">
                    {entry.purpose || 'No algorithm description is available.'}
                  </p>
                </CardContent>
              </Card>
            ))}
            {!error && filteredAlgorithms.length === 0 && (
              <Card className="flex items-center justify-center p-6 border-dashed bg-gray-50/50 dark:bg-gray-900/50">
                <p className="text-gray-400 text-sm max-w-[240px] text-center">
                  No algorithms matched your filters.
                </p>
              </Card>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

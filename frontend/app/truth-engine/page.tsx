'use client';

import Link from "next/link";
import React, { useEffect, useMemo, useState } from 'react';
import { PageLayout } from "@/components/ui/page-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { api } from '@/lib/api';

interface TraceRunRecord {
  run_id: string;
  status?: string;
  created_at?: string;
  input_message?: string;
  scores?: {
    confidence?: number;
    entropy?: number;
    bias_risk?: number;
  };
}

function statusToVerdict(status?: string): 'True' | 'False' | 'Uncertain' {
  if (status === 'pass' || status === 'completed') return 'True';
  if (status === 'fail' || status === 'failed') return 'False';
  return 'Uncertain';
}

export default function TruthEnginePage() {
  const [runs, setRuns] = useState<TraceRunRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function loadRuns() {
      setError(null);
      try {
        const data = await api.trace.list(30);
        if (!cancelled) {
          setRuns((data || []) as TraceRunRecord[]);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load trace runs');
          setRuns([]);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    void loadRuns();
    return () => {
      cancelled = true;
    };
  }, []);

  const metrics = useMemo(() => {
    const confidenceValues = runs
      .map((entry) => entry.scores?.confidence)
      .filter((value): value is number => typeof value === 'number');
    const avgConfidence = confidenceValues.length
      ? confidenceValues.reduce((sum, value) => sum + value, 0) / confidenceValues.length
      : 0;

    const failCount = runs.filter((entry) => entry.status === 'fail' || entry.status === 'failed').length;
    const conflictRate = runs.length > 0 ? (failCount / runs.length) * 100 : 0;

    return {
      truthScore: avgConfidence * 100,
      activeRuns: runs.length,
      conflictRate,
    };
  }, [runs]);

  return (
    <PageLayout
      title="Truth Engine"
      description="Live validation telemetry from stored trace runs."
      breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Truth Engine" }]}
    >
      <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        {error && (
          <Card className="border-red-500/30 bg-red-500/10">
            <CardContent className="p-4 text-sm text-red-300">{error}</CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="fluent-acrylic border-none bg-blue-600/90 text-white shadow-[0_8px_32px_rgba(37,99,235,0.3)] overflow-hidden relative group">
            <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent pointer-events-none" />
            <CardHeader className="relative z-10">
              <CardTitle className="text-white/90 text-sm font-bold tracking-wider uppercase">Truth Score</CardTitle>
              <CardDescription className="text-blue-100/70">Average run confidence across available traces.</CardDescription>
            </CardHeader>
            <CardContent className="relative z-10">
              <div className="text-6xl font-bold mb-4 tracking-tighter">
                {loading ? '--' : `${metrics.truthScore.toFixed(1)}%`}
              </div>
              <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/20 w-fit text-xs font-bold backdrop-blur-md border border-white/10">
                <span className="h-1.5 w-1.5 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.8)]"></span>
                LIVE_CALCULATION
              </div>
            </CardContent>
          </Card>

          <Card className="fluent-acrylic border-white/10 shadow-xl hover:bg-white/5 transition-all">
            <CardHeader>
              <CardTitle className="text-gray-100 text-sm font-bold tracking-wider uppercase">Active Trace Runs</CardTitle>
              <CardDescription className="text-gray-500">Run records available in trace storage.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold mb-2 text-white">{loading ? '--' : metrics.activeRuns}</div>
              <div className="flex items-center gap-2 text-xs text-blue-400 font-mono">
                <span className="animate-pulse">●</span>
                trace/run inventory
              </div>
            </CardContent>
          </Card>

          <Card className="fluent-acrylic border-white/10 shadow-xl hover:bg-white/5 transition-all">
            <CardHeader>
              <CardTitle className="text-gray-100 text-sm font-bold tracking-wider uppercase">Conflict Rate</CardTitle>
              <CardDescription className="text-gray-500">Runs with failed verdict status.</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold mb-2 text-yellow-500">{loading ? '--' : `${metrics.conflictRate.toFixed(1)}%`}</div>
              <div className="flex items-center gap-2 text-xs text-gray-500 font-mono">
                computed from status distribution
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="fluent-acrylic border-white/10 overflow-hidden shadow-2xl">
          <CardHeader className="border-b border-white/5 bg-white/5">
            <CardTitle className="text-gray-100">Validation Log</CardTitle>
            <CardDescription className="text-gray-500">Recent trace validations from `/api/v1/trace/runs`.</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
              <TableHeader className="bg-white/5">
                <TableRow className="hover:bg-transparent border-white/5">
                  <TableHead className="text-gray-400 font-bold text-xs uppercase tracking-wider">Run ID</TableHead>
                  <TableHead className="text-gray-400 font-bold text-xs uppercase tracking-wider">Input Claim</TableHead>
                  <TableHead className="text-gray-400 font-bold text-xs uppercase tracking-wider">Status</TableHead>
                  <TableHead className="text-gray-400 font-bold text-xs uppercase tracking-wider">Verdict</TableHead>
                  <TableHead className="text-right text-gray-400 font-bold text-xs uppercase tracking-wider">Confidence</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {!loading && runs.slice(0, 20).map((entry) => {
                  const verdict = statusToVerdict(entry.status);
                  const confidence = typeof entry.scores?.confidence === 'number' ? `${(entry.scores.confidence * 100).toFixed(1)}%` : '--';
                  return (
                    <TableRow key={entry.run_id} className="border-white/5 hover:bg-white/5 transition-colors group">
                      <TableCell className="font-mono text-[10px] text-gray-500">
                        <Link href={`/runs/view?id=${entry.run_id}`} className="text-blue-400 hover:text-blue-300 transition-colors">
                          {entry.run_id.slice(0, 8)}
                        </Link>
                      </TableCell>
                      <TableCell className="font-medium text-gray-200">
                        {(entry.input_message || 'No captured input').slice(0, 96)}
                      </TableCell>
                      <TableCell className="text-xs text-gray-400 font-mono">{entry.status || 'unknown'}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={cn(
                            "px-2 py-0 h-5 text-[10px] font-bold border-none",
                            verdict === 'True' ? 'bg-green-500/20 text-green-400' :
                            verdict === 'False' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'
                          )}
                        >
                          {verdict.toUpperCase()}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs text-blue-400 font-bold">{confidence}</TableCell>
                    </TableRow>
                  );
                })}
                {!loading && runs.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-sm text-gray-500 p-6">
                      No trace runs available yet.
                    </TableCell>
                  </TableRow>
                )}
                {loading && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-sm text-gray-500 p-6">
                      Loading trace runs...
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}

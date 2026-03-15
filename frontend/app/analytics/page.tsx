'use client';

import useSWR from 'swr';
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart3 } from "lucide-react";

interface Pillar {
  uid: string;
  pillar_id: string;
  name: string;
}

interface AxisGroup {
  title: string;
  rangeLabel: string;
  min: number;
  max: number;
}

const AXIS_GROUPS: AxisGroup[] = [
  { title: 'Core', rangeLabel: '1-5', min: 1, max: 5 },
  { title: 'Crosswalk', rangeLabel: '6-7', min: 6, max: 7 },
  { title: 'Personas', rangeLabel: '8-11', min: 8, max: 11 },
  { title: 'Context', rangeLabel: '12-13', min: 12, max: 13 },
  { title: 'Enterprise', rangeLabel: '14-17', min: 14, max: 17 },
];

function parseAxisNumber(value: string): number | null {
  const match = String(value).match(/\d+/);
  if (!match) return null;
  const parsed = Number.parseInt(match[0], 10);
  return Number.isNaN(parsed) ? null : parsed;
}

export default function AnalyticsPage() {
  const { data: pillars, isLoading, error } = useSWR<Pillar[]>('knowledge-pillars', () => api.knowledge.pillars());

  return (
    <div className="min-h-full bg-background text-foreground font-sans">
      <div className="min-h-full bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">

        {/* Acrylic Header */}
        <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center justify-between px-8 backdrop-blur-3xl">
          <div className="flex items-center gap-3">
            <div className="bg-purple-500/10 p-2 rounded-lg border border-purple-500/20">
              <BarChart3 className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <h1 className="text-title font-bold text-slate-900 dark:text-gray-100">Analytics</h1>
              <div className="text-[10px] text-slate-500 dark:text-gray-500 font-mono uppercase tracking-widest">17-Axis Framework Coverage</div>
            </div>
          </div>
        </div>

        <div className="max-w-[1600px] w-full mx-auto p-8 space-y-8 animate-connected-enter">

          {error && (
            <Card className="border-red-500/30 bg-red-500/10">
              <CardContent className="p-4 text-sm text-red-600 dark:text-red-300">
                Failed to load analytics data: {error instanceof Error ? error.message : 'Unknown error'}
              </CardContent>
            </Card>
          )}

          <Card className="fluent-card">
            <CardHeader>
              <CardTitle>17-Axis Framework Coverage</CardTitle>
              <CardDescription>Data shown only from indexed pillars returned by live queries.</CardDescription>
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
                  {AXIS_GROUPS.map((group) => {
                    const groupPillars = (pillars || []).filter((entry) => {
                      const axis = parseAxisNumber(entry.pillar_id);
                      return axis !== null && axis >= group.min && axis <= group.max;
                    });

                    return (
                      <div key={group.title} className="space-y-4">
                        <h4 className="text-xs font-bold text-slate-500 dark:text-gray-500 uppercase tracking-wider">
                          {group.title} ({group.rangeLabel})
                        </h4>
                        <div className="space-y-2">
                          {groupPillars.map((entry) => (
                            <div key={entry.uid} className="flex items-center justify-between p-2 bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/5 rounded-lg">
                              <div className="flex items-center gap-2">
                                <Badge variant="outline" className="min-w-10 h-6 rounded-full flex items-center justify-center p-0 text-[10px] font-mono">
                                  {entry.pillar_id}
                                </Badge>
                                <span className="text-sm font-medium text-slate-700 dark:text-gray-300">{entry.name}</span>
                              </div>
                              <div className="text-[10px] text-slate-400 dark:text-gray-600 font-mono uppercase">Indexed</div>
                            </div>
                          ))}
                          {groupPillars.length === 0 && (
                            <p className="text-xs text-slate-500 dark:text-muted-foreground italic">
                              No indexed nodes in this range.
                            </p>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

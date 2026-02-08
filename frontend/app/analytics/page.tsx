'use client';

import useSWR from 'swr';
import { api } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

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
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8">
      <div className="container mx-auto max-w-7xl">
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Analytics</h1>
          <p className="text-gray-500">Live axis and pillar distribution from indexed data.</p>
        </header>

        {error && (
          <Card className="mb-6 border-red-500/30 bg-red-500/10">
            <CardContent className="p-4 text-sm text-red-600 dark:text-red-300">
              Failed to load analytics data: {error instanceof Error ? error.message : 'Unknown error'}
            </CardContent>
          </Card>
        )}

        <Card>
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
                      <h4 className="text-sm font-semibold text-gray-500 uppercase">
                        {group.title} ({group.rangeLabel})
                      </h4>
                      <div className="space-y-2">
                        {groupPillars.map((entry) => (
                          <div key={entry.uid} className="flex items-center justify-between p-2 bg-gray-100 dark:bg-gray-800 rounded">
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className="min-w-10 h-6 rounded-full flex items-center justify-center p-0">
                                {entry.pillar_id}
                              </Badge>
                              <span className="text-sm font-medium">{entry.name}</span>
                            </div>
                            <div className="text-xs text-gray-500">Indexed</div>
                          </div>
                        ))}
                        {groupPillars.length === 0 && (
                          <p className="text-xs text-muted-foreground">
                            No indexed nodes returned for this axis range.
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
    </main>
  );
}

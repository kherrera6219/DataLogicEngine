'use client';

import React from 'react';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import useSWR from 'swr';
import { api } from '@/lib/api';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertCircle } from 'lucide-react';

export function ComplianceTrendChart() {
  const { data: trendData, isLoading, error } = useSWR('analytics-trends-sessions', () => 
    api.analytics.trends('sessions', 14)
  );

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const data = (trendData as any)?.data?.data_points || [];

  return (
    <Card className="glass-card overflow-hidden">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg">Compliance & Intelligence Trends</CardTitle>
            <CardDescription>Activity across the 17-axis framework (14-day history)</CardDescription>
          </div>
          <div className="flex gap-2">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="text-xs text-muted-foreground">Sessions</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="h-[300px] w-full pt-4">
        {isLoading ? (
          <Skeleton className="w-full h-full" />
        ) : error ? (
          <div className="flex items-center justify-center h-full gap-2 text-sm text-red-500">
            <AlertCircle className="h-4 w-4" />
            <span>Failed to load trend data</span>
          </div>
        ) : data.length === 0 ? (
          <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
            No data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data}>
              <defs>
                <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
              <XAxis 
                dataKey="date" 
                axisLine={false} 
                tickLine={false} 
                tick={{fontSize: 10}} 
                tickFormatter={(str) => new Date(str).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
              />
              <YAxis axisLine={false} tickLine={false} tick={{fontSize: 10}} />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'rgba(17, 24, 39, 0.8)', 
                  border: '1px solid rgba(255,255,255,0.1)', 
                  borderRadius: '12px',
                  backdropFilter: 'blur(8px)',
                  color: '#fff'
                }}
                itemStyle={{ color: '#60a5fa' }}
              />
              <Area 
                type="monotone" 
                dataKey="value" 
                name="Sessions"
                stroke="#3b82f6" 
                fillOpacity={1} 
                fill="url(#colorValue)" 
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

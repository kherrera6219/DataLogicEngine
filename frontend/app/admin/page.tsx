'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Users, Activity, ShieldAlert, Server,
  RefreshCw, Database
} from "lucide-react";
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { request } from '@/lib/api';

interface AdminStats {
  user_count: number;
  active_users: number;
  node_count: number;
  edge_count: number;
  simulation_count: number;
}

interface AdminDashboardPayload {
  stats: AdminStats;
}

export default function AdminPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const isAdmin = Boolean(user?.is_admin || user?.role === 'admin' || user?.role === 'owner');

  const [dashboard, setDashboard] = useState<AdminDashboardPayload | null>(null);
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAdminData = React.useCallback(async () => {
    setLoadingData(true);
    setError(null);
    try {
      const dashboardResponse = await request<AdminDashboardPayload>('/admin/dashboard');
      setDashboard(dashboardResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load admin data');
    } finally {
      setLoadingData(false);
    }
  }, []);

  useEffect(() => {
    if (!isLoading && !isAdmin) {
      router.replace('/dashboard?error=admin_required');
    }
  }, [isAdmin, isLoading, router]);

  useEffect(() => {
    if (isLoading || !isAdmin) return;
    let cancelled = false;
    async function init() {
      await loadAdminData();
      if (cancelled) return;
    }
    void init();
    return () => { cancelled = true; };
  }, [isAdmin, isLoading, loadAdminData]);

  const stats = dashboard?.stats;
  const activeUsers = stats?.active_users ?? 0;
  const totalUsers = stats?.user_count ?? 0;

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-foreground">
        <p className="text-sm text-muted-foreground">Checking administrative access...</p>
      </div>
    );
  }

  if (!isAdmin) {
    return null;
  }

  return (
    <div className="min-h-full bg-background text-foreground font-sans">
      <div className="min-h-full bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">
        <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center justify-between px-8 backdrop-blur-3xl">
          <div className="flex items-center gap-3">
            <div className="bg-red-900/10 p-2 rounded-lg border border-red-500/20">
              <ShieldAlert className="h-5 w-5 text-red-500" />
            </div>
            <div>
              <h1 className="text-title font-bold text-slate-900 dark:text-gray-100">System Administration</h1>
              <div className="text-[10px] text-slate-500 dark:text-gray-500 font-mono flex items-center gap-2">
                LIVE_DATA <span className="text-green-500">●</span>
              </div>
            </div>
          </div>
          <Button
            variant="outline"
            size="sm"
            className="border-slate-300/70 dark:border-white/10 bg-white/70 dark:bg-white/5"
            onClick={() => void loadAdminData()}
            disabled={loadingData}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loadingData ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        <div className="max-w-[1600px] w-full mx-auto p-8 space-y-8 animate-connected-enter">
          {error && (
            <Card className="border-red-500/20 bg-red-500/5">
              <CardContent className="p-4 text-sm text-red-600 dark:text-red-300">
                Failed to load admin telemetry: {error}
              </CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {[
              { label: 'Total Users', value: totalUsers, sub: `${activeUsers} active`, icon: Users, color: 'text-blue-400' },
              { label: 'Knowledge Nodes', value: stats?.node_count ?? 0, sub: `${stats?.edge_count ?? 0} edges`, icon: Database, color: 'text-emerald-400' },
              { label: 'Simulation Runs', value: stats?.simulation_count ?? 0, sub: 'Stored in local profile', icon: Activity, color: 'text-purple-400' },
              { label: 'User Health', value: `${activeUsers}/${totalUsers || 0}`, sub: 'Active ratio', icon: Server, color: 'text-amber-400' },
            ].map((metric) => (
              <Card key={metric.label} className="fluent-card hover:-translate-y-1">
                <CardContent className="p-5 flex items-center justify-between">
                  <div>
                    <div className="text-xs text-slate-500 dark:text-gray-500 uppercase tracking-wider mb-1 font-semibold">{metric.label}</div>
                    <div className="text-2xl font-bold font-mono text-slate-900 dark:text-gray-200">{metric.value}</div>
                    <div className="text-[10px] text-slate-500 dark:text-gray-500 mt-1">{metric.sub}</div>
                  </div>
                  <metric.icon className={`h-8 w-8 opacity-30 ${metric.color}`} />
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

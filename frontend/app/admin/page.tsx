'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Users, Activity, ShieldAlert, Server,
  MoreHorizontal, Search, RefreshCw, Database
} from "lucide-react";
import { Input } from "@/components/ui/input";
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

interface AdminUser {
  id: number;
  username: string;
  email?: string;
  role?: string;
  active?: boolean;
  created_at?: string;
  last_login?: string;
}

interface AdminDashboardPayload {
  stats: AdminStats;
  recent_users: AdminUser[];
}

interface AdminUsersPayload {
  users: AdminUser[];
  counts?: Record<string, number>;
}

function formatRelative(dateString?: string): string {
  if (!dateString) return 'Never';
  const target = new Date(dateString).getTime();
  if (Number.isNaN(target)) return 'Unknown';
  const diffMs = Date.now() - target;
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function AdminPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const isAdmin = Boolean(user?.is_admin || user?.role === 'admin' || user?.role === 'owner');

  const [query, setQuery] = useState('');
  const [dashboard, setDashboard] = useState<AdminDashboardPayload | null>(null);
  const [usersData, setUsersData] = useState<AdminUsersPayload>({ users: [] });
  const [loadingData, setLoadingData] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAdminData = React.useCallback(async () => {
    setLoadingData(true);
    setError(null);
    try {
      const [dashboardResponse, usersResponse] = await Promise.all([
        request<AdminDashboardPayload>('/admin/dashboard'),
        request<AdminUsersPayload>('/admin/users?page=1&per_page=100'),
      ]);
      setDashboard(dashboardResponse);
      setUsersData(usersResponse);
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
    void loadAdminData();
  }, [isAdmin, isLoading, loadAdminData]);

  const filteredUsers = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return usersData.users;
    return usersData.users.filter((entry) =>
      `${entry.username || ''} ${entry.email || ''} ${entry.role || ''}`.toLowerCase().includes(needle)
    );
  }, [query, usersData.users]);

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

  const stats = dashboard?.stats;
  const roleCounts = usersData.counts || {};
  const activeUsers = stats?.active_users ?? usersData.users.filter((entry) => entry.active).length;
  const totalUsers = stats?.user_count ?? usersData.users.length;

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

          <Card className="fluent-card">
            <CardHeader className="border-b border-white/5 pb-4">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div>
                  <CardTitle className="text-base font-semibold text-slate-900 dark:text-gray-200">User Management</CardTitle>
                  <CardDescription className="text-xs text-slate-600 dark:text-gray-500 mt-1">
                    Real user profiles and role assignments from `/api/v1/admin/users`.
                  </CardDescription>
                </div>
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500 dark:text-gray-500" />
                    <Input
                      placeholder="Search users..."
                      className="h-9 pl-9 w-72 bg-white/80 dark:bg-black/20 border-slate-300/70 dark:border-white/10 text-sm"
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                    />
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    {Object.entries(roleCounts).map(([role, count]) => (
                      <Badge key={role} variant="outline" className="bg-blue-500/5 text-blue-500 border-blue-500/20">
                        {role}: {count}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-100/80 dark:bg-black/20 text-slate-600 dark:text-gray-500 font-medium border-b border-white/5">
                  <tr>
                    <th className="p-4 font-medium pl-6">User Identity</th>
                    <th className="p-4 font-medium">Role</th>
                    <th className="p-4 font-medium">Status</th>
                    <th className="p-4 font-medium">Last Active</th>
                    <th className="p-4 font-medium text-right pr-6">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-slate-700 dark:text-gray-300">
                  {filteredUsers.map((entry) => (
                    <tr key={entry.id} className="hover:bg-white/[0.02] transition-colors group">
                      <td className="p-4 pl-6">
                        <div className="font-semibold text-slate-900 dark:text-gray-200">{entry.username}</div>
                        <div className="text-xs text-slate-500 dark:text-gray-500">{entry.email || 'No email available'}</div>
                      </td>
                      <td className="p-4">
                        <Badge variant="outline" className="bg-blue-500/5 text-blue-500 border-blue-500/20 text-[10px] font-mono uppercase">
                          {entry.role || 'user'}
                        </Badge>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <div className={`h-1.5 w-1.5 rounded-full ${entry.active ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]' : 'bg-slate-400 dark:bg-gray-600'}`}></div>
                          <span className="capitalize text-xs text-slate-600 dark:text-gray-400">{entry.active ? 'active' : 'inactive'}</span>
                        </div>
                      </td>
                      <td className="p-4 font-mono text-xs text-slate-500 dark:text-gray-500">
                        {formatRelative(entry.last_login || entry.created_at)}
                      </td>
                      <td className="p-4 text-right pr-6">
                        <Button variant="ghost" size="icon" className="h-8 w-8 text-slate-500 dark:text-gray-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-200/70 dark:hover:bg-white/10 rounded-md">
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                  {!loadingData && filteredUsers.length === 0 && (
                    <tr>
                      <td className="p-6 text-sm text-slate-500 dark:text-gray-500" colSpan={5}>
                        No users matched your filters.
                      </td>
                    </tr>
                  )}
                  {loadingData && (
                    <tr>
                      <td className="p-6 text-sm text-slate-500 dark:text-gray-500" colSpan={5}>
                        Loading user telemetry...
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

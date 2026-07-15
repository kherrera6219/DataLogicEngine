'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { PageLayout } from "@/components/ui/page-layout";
import { Mail, Briefcase, Calendar, ShieldCheck } from "lucide-react";
import { useAuth } from '@/contexts/AuthContext';
import { request } from '@/lib/api';

interface UserDataSummary {
  account_created?: string;
  data_summary?: {
    total_simulations?: number;
  };
}

function formatDate(value?: string): string {
  if (!value) return 'Unknown';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return 'Unknown';
  return parsed.toLocaleDateString();
}

function getInitials(username?: string): string {
  if (!username) return 'U';
  const pieces = username.split(/\s+/).filter(Boolean);
  if (!pieces.length) return 'U';
  return pieces
    .slice(0, 2)
    .map((piece) => piece[0]?.toUpperCase() || '')
    .join('');
}

export default function ProfilePage() {
  const { user, isLoading } = useAuth();
  const [simulationCount, setSimulationCount] = useState<number | null>(null);

  useEffect(() => {
    if (!user) return;
    void request<UserDataSummary>('/user/data/summary')
      .then((summary) => {
        setSimulationCount(summary.data_summary?.total_simulations ?? 0);
      })
      .catch(() => {
        setSimulationCount(null);
      });
  }, [user]);

  const badgeLabel = useMemo(() => {
    if (!user) return 'NO SESSION';
    if (user.role === 'owner') return 'OWNER PRIVILEGES';
    if (user.is_admin || user.role === 'admin') return 'ADMIN PRIVILEGES';
    return 'STANDARD ACCESS';
  }, [user]);

  if (isLoading) {
    return (
      <PageLayout
        title="Authenticated Identity"
        description="Enterprise profile and security credentials."
        breadcrumbs={[{ label: "User Management" }, { label: "Profile" }]}
      >
        <div className="py-12 text-sm text-muted-foreground">Loading profile...</div>
      </PageLayout>
    );
  }

  if (!user) {
    return (
      <PageLayout
        title="Authenticated Identity"
        description="Enterprise profile and security credentials."
        breadcrumbs={[{ label: "User Management" }, { label: "Profile" }]}
      >
        <div className="py-12 text-sm text-muted-foreground">No authenticated user context was found.</div>
      </PageLayout>
    );
  }

  return (
    <PageLayout
      title="Authenticated Identity"
      description="Enterprise profile and security credentials."
      breadcrumbs={[{ label: "User Management" }, { label: "Profile" }]}
    >
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="lg:col-span-1 glass-card border-white/10 shadow-2xl" role="region" aria-label="Identity Overview">
          <CardHeader className="flex flex-col items-center text-center">
            <div className="relative group">
              <Avatar className="w-32 h-32 mb-4 border-2 border-white/5 group-hover:border-blue-500/50 transition-all duration-300">
                <AvatarFallback className="text-4xl bg-blue-600/20 text-blue-500 font-bold">{getInitials(user.username)}</AvatarFallback>
              </Avatar>
              <div className="absolute -bottom-2 -right-2 bg-blue-600 rounded-lg p-1 shadow-lg" aria-hidden="true">
                <ShieldCheck className="h-5 w-5 text-white" />
              </div>
            </div>
            <CardTitle className="text-2xl font-bold tracking-tight mt-4">{user.username}</CardTitle>
            <CardDescription className="text-blue-500 font-bold text-[10px] uppercase tracking-widest mt-1">
              {user.role || (user.is_admin ? 'admin' : 'user')}
            </CardDescription>
            <div className="mt-4">
              <Badge className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 font-bold px-3">{badgeLabel}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6 pt-6 border-t border-white/5">
            <div className="space-y-1">
              <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                <Mail className="h-3 w-3" aria-hidden="true" /> Registered Email
              </div>
              <div className="text-sm font-semibold">{user.email || 'No email set'}</div>
            </div>
            <div className="space-y-1">
              <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                <Briefcase className="h-3 w-3" aria-hidden="true" /> Department
              </div>
              <div className="text-sm font-semibold">{simulationCount !== null ? `${simulationCount} simulation records` : 'Not available'}</div>
            </div>
            <div className="space-y-1">
              <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                <Calendar className="h-3 w-3" aria-hidden="true" /> Identity Provisioned
              </div>
              <div className="text-sm font-semibold">{formatDate(user.created_at)}</div>
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-2 glass-card border-white/10 shadow-2xl" role="region" aria-label="Account Modifications">
          <CardHeader className="border-b border-white/5 mx-6 px-0 pb-6">
            <CardTitle className="text-xl font-bold">Profile Metadata</CardTitle>
            <CardDescription className="text-muted-foreground font-medium">Read-only account metadata from the active authenticated session. Identity changes are managed by the installed Windows owner account.</CardDescription>
          </CardHeader>
          <CardContent className="pt-8">
            <dl className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <dt className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Account name</dt>
                <dd className="mt-2 text-sm font-semibold">{user.username}</dd>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <dt className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Identity email</dt>
                <dd className="mt-2 text-sm font-semibold">{user.email || 'Not configured'}</dd>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <dt className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Access role</dt>
                <dd className="mt-2 text-sm font-semibold">{user.role || (user.is_admin ? 'admin' : 'user')}</dd>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                <dt className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">Provisioned</dt>
                <dd className="mt-2 text-sm font-semibold">{formatDate(user.created_at)}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}

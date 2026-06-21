'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { PageLayout } from "@/components/ui/page-layout";
import { Mail, Briefcase, Calendar, ShieldCheck, Save } from "lucide-react";
import { useAuth } from '@/contexts/AuthContext';
import { request } from '@/lib/api';
import { useToast } from '@/components/ui/use-toast';

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
  const { toast } = useToast();
  const [simulationCount, setSimulationCount] = useState<number | null>(null);
  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    email: '',
    role: '',
  });

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    const [firstName = user.username, ...rest] = user.username.split(/\s+/);
    setTimeout(() => {
      if (cancelled) return;
      setForm({
        firstName,
        lastName: rest.join(' '),
        email: user.email || '',
        role: user.role || (user.is_admin ? 'admin' : 'user'),
      });
    }, 0);
    return () => { cancelled = true; };
  }, [user]);

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

  const handleSave = (event: React.FormEvent) => {
    event.preventDefault();
    toast('Profile edits are not exposed yet. Account identity is managed by the OS-level (Windows) sign-in for the single owner.', 'info');
  };

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
              <div className="absolute -bottom-2 -right-2 bg-blue-600 rounded-lg p-1 shadow-lg" aria-label="Active Security Clearance">
                <ShieldCheck className="h-5 w-5 text-white" />
              </div>
            </div>
            <CardTitle className="text-2xl font-bold tracking-tight mt-4">{user.username}</CardTitle>
            <CardDescription className="text-blue-500 font-bold text-[10px] uppercase tracking-widest mt-1">
              {form.role || 'user'}
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
            <CardTitle className="text-xl font-bold">Profile Configurations</CardTitle>
            <CardDescription className="text-muted-foreground font-medium">Review account metadata sourced from your active authenticated session.</CardDescription>
          </CardHeader>
          <CardContent className="pt-8">
            <form className="space-y-8" onSubmit={handleSave}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest" htmlFor="first-name">Given Name</label>
                  <Input
                    id="first-name"
                    value={form.firstName}
                    onChange={(event) => setForm((prev) => ({ ...prev, firstName: event.target.value }))}
                    className="bg-white/5 border-white/10 h-11 rounded-xl focus-visible:ring-blue-500"
                  />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest" htmlFor="last-name">Surname</label>
                  <Input
                    id="last-name"
                    value={form.lastName}
                    onChange={(event) => setForm((prev) => ({ ...prev, lastName: event.target.value }))}
                    className="bg-white/5 border-white/10 h-11 rounded-xl focus-visible:ring-blue-500"
                  />
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest" htmlFor="email">Identity Email</label>
                <Input
                  id="email"
                  value={form.email}
                  onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
                  type="email"
                  className="bg-white/5 border-white/10 h-11 rounded-xl focus-visible:ring-blue-500"
                />
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest" htmlFor="job-title">Organizational Role</label>
                <Input
                  id="job-title"
                  value={form.role}
                  onChange={(event) => setForm((prev) => ({ ...prev, role: event.target.value }))}
                  className="bg-white/5 border-white/10 h-11 rounded-xl focus-visible:ring-blue-500"
                />
              </div>

              <div className="pt-6 border-t border-white/5 flex justify-end gap-3">
                <Button variant="ghost" type="button" className="h-11 px-8 rounded-xl font-bold hover:bg-white/5 text-muted-foreground transition-all">
                  Cancel
                </Button>
                <Button type="submit" className="h-11 px-8 rounded-xl bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/20 font-bold transition-all gap-2">
                  <Save className="h-4 w-4" /> Commit Changes
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}

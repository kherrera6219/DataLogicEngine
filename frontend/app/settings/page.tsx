'use client';

import React, { Suspense, useEffect, useState, useCallback } from 'react';
import { useSearchParams } from 'next/navigation';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Settings as SettingsIcon, Shield, Bell,
  Brain, Network, Monitor, Sun, Lock, Database, PanelLeftClose, PanelLeftOpen,
  RefreshCw
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { request } from '@/lib/api';
import { useTheme } from '@/contexts/ThemeContext';

interface NotificationPrefs {
  email_on_run_complete: boolean;
  email_on_run_failed: boolean;
  email_on_simulation_complete: boolean;
  inapp_run_complete: boolean;
  inapp_run_failed: boolean;
  inapp_simulation_complete: boolean;
  inapp_system_alerts: boolean;
  digest_frequency: string;
}

const DEFAULT_NOTIF_PREFS: NotificationPrefs = {
  email_on_run_complete: true,
  email_on_run_failed: true,
  email_on_simulation_complete: false,
  inapp_run_complete: true,
  inapp_run_failed: true,
  inapp_simulation_complete: true,
  inapp_system_alerts: true,
  digest_frequency: 'none',
};

const ApiOverlayConfig = dynamic(
  () => import("@/components/settings/ApiOverlayConfig").then((module) => ({ default: module.ApiOverlayConfig })),
  { loading: () => <div className="p-6 text-sm text-muted-foreground">Loading API overlay...</div> }
);
const ClientGatewayConfig = dynamic(
  () => import("@/components/settings/ClientGatewayConfig").then((module) => ({ default: module.ClientGatewayConfig })),
  { loading: () => <div className="p-6 text-sm text-muted-foreground">Loading Client Gateway...</div> }
);
const DatabaseSettings = dynamic(
  () => import("@/components/settings/DatabaseSettings"),
  { loading: () => <div className="p-6 text-sm text-muted-foreground">Loading storage configuration...</div> }
);
const AiModelSettings = dynamic(
  () => import("@/components/settings/AiModelSettings"),
  { loading: () => <div className="p-6 text-sm text-muted-foreground">Loading AI model controls...</div> }
);
const KnowledgeIngestionSettings = dynamic(
  () => import("@/components/settings/KnowledgeIngestionSettings"),
  { loading: () => <div className="p-6 text-sm text-muted-foreground">Loading knowledge ingestion...</div> }
);
const MemoryManagementSettings = dynamic(
  () => import("@/components/settings/MemoryManagementSettings"),
  { loading: () => <div className="p-6 text-sm text-muted-foreground">Loading memory controls...</div> }
);
const DatasetExporterSettings = dynamic(
  () => import("@/components/settings/DatasetExporterSettings"),
  { loading: () => <div className="p-6 text-sm text-muted-foreground">Loading dataset exporter...</div> }
);

interface UserDataSummary {
  account_created?: string;
  data_summary?: {
    total_simulations?: number;
  };
}

const enterpriseThemeOptions = [
  { id: 'default', label: 'Default' },
  { id: 'azure', label: 'Azure' },
  { id: 'government', label: 'Government' },
  { id: 'high-contrast', label: 'High Contrast' },
] as const;

function SettingsPageContent() {
  const searchParams = useSearchParams();
  const requestedTab = searchParams.get('tab');
  const [activeTab, setActiveTab] = useState(
    requestedTab && ['general', 'notifications', 'providers', 'gateway', 'storage', 'knowledge', 'security', 'ai', 'exporter'].includes(requestedTab)
      ? requestedTab
      : 'general',
  );
  const [summary, setSummary] = useState<UserDataSummary | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const { theme, setTheme, resolvedTheme, enterpriseTheme, setEnterpriseTheme } = useTheme();

  // Notification preferences state
  const [notifPrefs, setNotifPrefs] = useState<NotificationPrefs>(DEFAULT_NOTIF_PREFS);
  const [notifLoading, setNotifLoading] = useState(false);
  const [notifSaving, setNotifSaving] = useState(false);

  const fetchNotifPrefs = useCallback(async () => {
    setNotifLoading(true);
    try {
      const result = await request<{ preferences: NotificationPrefs }>('/user/notifications');
      setNotifPrefs(result.preferences ?? DEFAULT_NOTIF_PREFS);
    } catch {
      // keep defaults on error
    } finally {
      setNotifLoading(false);
    }
  }, []);

  const saveNotifPrefs = async (patch: Partial<NotificationPrefs>) => {
    const updated = { ...notifPrefs, ...patch };
    setNotifPrefs(updated);
    setNotifSaving(true);
    try {
      const result = await request<{ preferences: NotificationPrefs }>('/user/notifications', {
        method: 'POST',
        body: JSON.stringify(patch),
      });
      setNotifPrefs(result.preferences ?? updated);
    } catch {
      setNotifPrefs(notifPrefs); // revert on error
    } finally {
      setNotifSaving(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    void request<UserDataSummary>('/user/data/summary')
      .then((result) => {
        if (!cancelled) setSummary(result);
      })
      .catch(() => {
        if (!cancelled) setSummary(null);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (activeTab !== 'notifications') return;
    let cancelled = false;
    async function load() {
      await fetchNotifPrefs();
      if (cancelled) return;
    }
    void load();
    return () => { cancelled = true; };
  }, [activeTab, fetchNotifPrefs]);

  return (
    <div className="min-h-full bg-background text-foreground font-sans">
      <div className="min-h-full bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">
         
         {/* Acrylic Header */}
         <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center justify-between px-8 backdrop-blur-3xl">
            <h1 className="text-title font-bold text-slate-900 dark:text-gray-100 flex items-center gap-3">
               <SettingsIcon className="h-5 w-5 text-slate-500 dark:text-gray-400" />
               Settings 
               <span className="text-sm font-normal text-slate-500 dark:text-gray-500">/ Configuration</span>
            </h1>
            <span className="text-xs text-slate-500 dark:text-gray-400">Changes save within each section</span>
         </div>

         <div className="max-w-[1600px] w-full mx-auto p-8 space-y-8 animate-connected-enter">
            
            <Tabs value={activeTab} onValueChange={setActiveTab} className="flex gap-8 items-start">
               
               {/* Settings Sidebar */}
               <div className={`${isSidebarCollapsed ? "w-16" : "w-64"} shrink-0 space-y-4 sticky top-24 transition-all duration-300`}>
                  <Button
                    data-testid="settings-sidebar-toggle"
                    variant="outline"
                    size="sm"
                    onClick={() => setIsSidebarCollapsed((prev) => !prev)}
                    className="w-full justify-center gap-2 border-slate-300/70 dark:border-white/10 bg-white/80 dark:bg-black/20"
                    aria-label={isSidebarCollapsed ? "Expand settings sidebar" : "Collapse settings sidebar"}
                    title={isSidebarCollapsed ? "Expand settings sidebar" : "Collapse settings sidebar"}
                  >
                    {isSidebarCollapsed ? <PanelLeftOpen className="h-4 w-4" /> : <PanelLeftClose className="h-4 w-4" />}
                    {!isSidebarCollapsed && <span>Collapse</span>}
                  </Button>
                  <TabsList className="flex flex-col h-auto bg-transparent space-y-1 p-0">
                     {[
                        { id: 'general', label: 'General', icon: Monitor },
                        { id: 'notifications', label: 'Notifications', icon: Bell },
                        { id: 'providers', label: 'Provider Connections', icon: Brain },
                        { id: 'gateway', label: 'Client Gateway', icon: Network },
                        { id: 'storage', label: 'Storage', icon: Database },
                        { id: 'knowledge', label: 'Knowledge', icon: Database },
                        { id: 'security', label: 'Security', icon: Shield },
                        { id: 'ai', label: 'AI Models', icon: Brain },
                        { id: 'exporter', label: 'Dataset Exporter', icon: Database },
                     ].map(tab => (
                        <TabsTrigger 
                           key={tab.id} 
                           value={tab.id}
                           className={`w-full ${isSidebarCollapsed ? "justify-center px-0" : "justify-start px-4"} py-3 h-auto text-sm font-medium text-slate-700 dark:text-gray-300 data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-lg hover:bg-slate-200/70 dark:hover:bg-white/5 rounded-xl transition-all`}
                           title={tab.label}
                        >
                           <tab.icon className={`h-4 w-4 ${isSidebarCollapsed ? "" : "mr-3"}`} />
                           {!isSidebarCollapsed && tab.label}
                        </TabsTrigger>
                     ))}
                  </TabsList>

                  {!isSidebarCollapsed && (
                    <Card className="fluent-card bg-gradient-to-br from-purple-900/20 to-blue-900/20 border-blue-500/20">
                       <CardContent className="p-4 space-y-3">
                          <div className="flex items-center gap-2 text-blue-400 font-semibold text-sm">
                             <Shield className="h-4 w-4" /> Enterprise Protected
                          </div>
                          <p className="text-xs text-slate-600 dark:text-gray-400">Settings are enforced by global registry policies.</p>
                       </CardContent>
                    </Card>
                  )}
               </div>

               {/* Content Area */}
               <div className="flex-1 space-y-6 min-w-0">
                  
                  {/* GENERAL SETTINGS */}
                  <TabsContent value="general" className="space-y-6 m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                     <Card className="fluent-card">
                        <CardHeader>
                           <CardTitle>Appearance</CardTitle>
                           <CardDescription>Customize the interface look and feel.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                           <div className="flex items-center justify-between p-4 rounded-xl bg-white/70 dark:bg-black/20 border border-slate-200 dark:border-white/5">
                              <div className="flex items-center gap-4">
                                 <div className="h-10 w-10 rounded-full bg-slate-200/70 dark:bg-white/5 flex items-center justify-center">
                                    <Sun className="h-5 w-5 text-yellow-400" />
                                 </div>
                                 <div>
                                    <div className="font-medium text-slate-900 dark:text-gray-200">Theme Preference</div>
                                    <div className="text-xs text-slate-500 dark:text-gray-500">Select your preferred system theme</div>
                                 </div>
                              </div>
                              <div className="flex gap-2">
                                 <Button
                                   variant="outline"
                                   size="sm"
                                   onClick={() => setTheme('dark')}
                                   className={resolvedTheme === 'dark' && theme !== 'light' ? "bg-blue-600/20 border-blue-500/50 text-blue-400" : "text-slate-700 dark:text-gray-400"}
                                 >
                                   Dark
                                 </Button>
                                 <Button
                                   variant="ghost"
                                   size="sm"
                                   onClick={() => setTheme('light')}
                                   className={resolvedTheme === 'light' ? "bg-blue-600/20 border-blue-500/50 text-blue-400" : "text-slate-600 dark:text-gray-500"}
                                 >
                                   Light
                                 </Button>
                              </div>
                           </div>
                           <div className="space-y-3 p-4 rounded-xl bg-white/70 dark:bg-black/20 border border-slate-200 dark:border-white/5">
                              <div className="flex items-center justify-between gap-3">
                                <div>
                                <div className="font-medium text-slate-900 dark:text-gray-200">Enterprise Theme Preset</div>
                                <div className="text-xs text-slate-500 dark:text-gray-500">Apply organization-level token overrides.</div>
                                </div>
                                <div
                                  className="h-8 w-8 rounded-full border border-white/20 shadow-inner"
                                  style={{ backgroundColor: 'var(--accent)' }}
                                  aria-label="Current accent preview"
                                  title="Current accent preview"
                                />
                              </div>
                              <div className="grid grid-cols-2 gap-2">
                                {enterpriseThemeOptions.map((option) => (
                                  <Button
                                    key={option.id}
                                    variant="outline"
                                    size="sm"
                                    onClick={() => setEnterpriseTheme(option.id)}
                                    className={
                                      enterpriseTheme === option.id
                                        ? 'bg-blue-600/20 border-blue-500/50 text-blue-400'
                                        : 'text-slate-700 dark:text-gray-400'
                                    }
                                  >
                                    {option.label}
                                  </Button>
                                ))}
                              </div>
                           </div>
                        </CardContent>
                     </Card>
                  </TabsContent>

                  {/* NOTIFICATIONS */}
                  <TabsContent value="notifications" className="space-y-6 m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                     <Card className="fluent-card">
                        <CardHeader className="flex flex-row items-center justify-between">
                           <div>
                             <CardTitle>Notification Preferences</CardTitle>
                             <CardDescription>Manage how and when you receive system alerts.</CardDescription>
                           </div>
                           <Button variant="ghost" size="sm" onClick={fetchNotifPrefs} disabled={notifLoading}>
                             <RefreshCw className={`h-4 w-4 ${notifLoading ? 'animate-spin' : ''}`} />
                           </Button>
                        </CardHeader>
                        <CardContent className="space-y-6">
                          {notifLoading ? (
                            <div className="flex items-center justify-center py-8">
                              <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                          ) : (
                            <>
                              {/* Email Notifications */}
                              <div className="space-y-3">
                                <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 uppercase tracking-wide">Email Alerts</h3>
                                {([
                                  { key: 'email_on_run_complete', label: 'Run completed', desc: 'Notify when an analysis run finishes successfully.' },
                                  { key: 'email_on_run_failed', label: 'Run failed', desc: 'Notify when a run errors or times out.' },
                                  { key: 'email_on_simulation_complete', label: 'Simulation complete', desc: 'Notify when a simulation finishes.' },
                                ] as const).map(({ key, label, desc }) => (
                                  <div key={key} className="flex items-center justify-between p-3 rounded-xl bg-white/50 dark:bg-black/20 border border-slate-200 dark:border-white/5">
                                    <div>
                                      <Label htmlFor={key} className="font-medium text-slate-800 dark:text-gray-200">{label}</Label>
                                      <p className="text-xs text-slate-500 dark:text-gray-500">{desc}</p>
                                    </div>
                                    <Switch
                                      id={key}
                                      checked={notifPrefs[key]}
                                      onCheckedChange={(v) => void saveNotifPrefs({ [key]: v })}
                                      disabled={notifSaving}
                                    />
                                  </div>
                                ))}
                              </div>

                              {/* In-App Notifications */}
                              <div className="space-y-3">
                                <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 uppercase tracking-wide">In-App Alerts</h3>
                                {([
                                  { key: 'inapp_run_complete', label: 'Run completed', desc: 'Show banner when a run finishes.' },
                                  { key: 'inapp_run_failed', label: 'Run failed', desc: 'Show banner when a run errors.' },
                                  { key: 'inapp_simulation_complete', label: 'Simulation complete', desc: 'Show banner when simulation finishes.' },
                                  { key: 'inapp_system_alerts', label: 'System alerts', desc: 'Show important system-level notices.' },
                                ] as const).map(({ key, label, desc }) => (
                                  <div key={key} className="flex items-center justify-between p-3 rounded-xl bg-white/50 dark:bg-black/20 border border-slate-200 dark:border-white/5">
                                    <div>
                                      <Label htmlFor={`ia-${key}`} className="font-medium text-slate-800 dark:text-gray-200">{label}</Label>
                                      <p className="text-xs text-slate-500 dark:text-gray-500">{desc}</p>
                                    </div>
                                    <Switch
                                      id={`ia-${key}`}
                                      checked={notifPrefs[key]}
                                      onCheckedChange={(v) => void saveNotifPrefs({ [key]: v })}
                                      disabled={notifSaving}
                                    />
                                  </div>
                                ))}
                              </div>

                              {/* Digest */}
                              <div className="space-y-2">
                                <h3 className="text-sm font-semibold text-slate-700 dark:text-gray-300 uppercase tracking-wide">Digest Frequency</h3>
                                <Select
                                  value={notifPrefs.digest_frequency}
                                  onChange={(e) => void saveNotifPrefs({ digest_frequency: e.target.value })}
                                  disabled={notifSaving}
                                >
                                  <SelectTrigger className="w-48">
                                    <SelectValue />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="none">No digest</SelectItem>
                                    <SelectItem value="daily">Daily summary</SelectItem>
                                    <SelectItem value="weekly">Weekly summary</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                            </>
                          )}
                        </CardContent>
                     </Card>
                  </TabsContent>

                  {/* PROVIDER CONNECTIONS */}
                  <TabsContent value="providers" className="space-y-6 m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                     <div className="space-y-1 mb-6">
                        <h2 className="text-lg font-bold">Provider Connections</h2>
                        <p className="text-sm text-slate-600 dark:text-gray-400">Store and validate outbound OpenAI or Google credentials.</p>
                     </div>
                     <ApiOverlayConfig />
                  </TabsContent>

                  {/* CLIENT GATEWAY */}
                  <TabsContent value="gateway" className="space-y-6 m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                     <ClientGatewayConfig />
                  </TabsContent>

                  {/* STORAGE */}
                  <TabsContent value="storage" className="m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                     <DatabaseSettings />
                  </TabsContent>

                  {/* KNOWLEDGE INGESTION */}
                  <TabsContent value="knowledge" className="m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                     <KnowledgeIngestionSettings />
                     <div className="mt-6"><MemoryManagementSettings /></div>
                  </TabsContent>

                  {/* SECURITY */}
                  <TabsContent value="security" className="m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                     <Card className="fluent-card">
                        <CardHeader>
                           <CardTitle className="flex items-center gap-2"><Lock className="h-5 w-5" /> Privacy & Security</CardTitle>
                           <CardDescription>Current account and local data posture.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                           <div className="rounded-xl border border-slate-300/70 dark:border-white/10 bg-slate-50 dark:bg-black/20 p-4">
                              <div className="text-sm text-slate-700 dark:text-gray-300">Local simulation records</div>
                              <div className="text-2xl font-bold text-slate-900 dark:text-white">{summary?.data_summary?.total_simulations ?? 'Unknown'}</div>
                           </div>
                           <div className="rounded-xl border border-slate-300/70 dark:border-white/10 bg-slate-50 dark:bg-black/20 p-4">
                              <div className="text-sm text-slate-700 dark:text-gray-300">Account provisioned</div>
                              <div className="text-base font-semibold text-slate-900 dark:text-white">{summary?.account_created ? new Date(summary.account_created).toLocaleDateString() : 'Unknown'}</div>
                           </div>
                           <Button asChild className="bg-blue-600 hover:bg-blue-700">
                             <Link href="/settings/privacy">Open Privacy Controls</Link>
                           </Button>
                        </CardContent>
                     </Card>
                  </TabsContent>

                  {/* AI MODELS */}
                  <TabsContent value="ai" className="m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                     <AiModelSettings />
                  </TabsContent>

                  {/* DATASET EXPORTER */}
                  <TabsContent value="exporter" className="m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                     <DatasetExporterSettings />
                  </TabsContent>

               </div>
            </Tabs>
         </div>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  return (
    <Suspense fallback={<div className="p-8 text-sm text-muted-foreground">Loading settings…</div>}>
      <SettingsPageContent />
    </Suspense>
  );
}

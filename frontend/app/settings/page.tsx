'use client';

import React, { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import Link from 'next/link';
import { Button } from "@/components/ui/button";

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Settings as SettingsIcon, Shield, Bell, Save, 
  Brain, Network, Monitor, Sun, Lock, Database, PanelLeftClose, PanelLeftOpen
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { request } from '@/lib/api';
import { useTheme } from '@/contexts/ThemeContext';

const ApiOverlayConfig = dynamic(
  () => import("@/components/settings/ApiOverlayConfig").then((module) => ({ default: module.ApiOverlayConfig })),
  { loading: () => <div className="p-6 text-sm text-muted-foreground">Loading API overlay...</div> }
);
const DatabaseSettings = dynamic(
  () => import("@/components/settings/DatabaseSettings"),
  { loading: () => <div className="p-6 text-sm text-muted-foreground">Loading storage configuration...</div> }
);
const AiModelSettings = dynamic(
  () => import("@/components/settings/AiModelSettings"),
  { loading: () => <div className="p-6 text-sm text-muted-foreground">Loading AI model controls...</div> }
);

interface UserDataSummary {
  account_created?: string;
  data_summary?: {
    total_simulations?: number;
  };
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("general");
  const [summary, setSummary] = useState<UserDataSummary | null>(null);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const { theme, setTheme, resolvedTheme } = useTheme();

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
            <Button className="bg-blue-600 hover:bg-blue-700 font-bold shadow-lg shadow-blue-900/20">
               <Save className="h-4 w-4 mr-2" /> Save Changes
            </Button>
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
                        { id: 'api', label: 'API Gateway', icon: Network },
                        { id: 'storage', label: 'Storage', icon: Database },
                        { id: 'security', label: 'Security', icon: Shield },
                        { id: 'ai', label: 'AI Models', icon: Brain },
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
                        </CardContent>
                     </Card>
                  </TabsContent>

                  {/* NOTIFICATIONS */}
                  <TabsContent value="notifications" className="space-y-6 m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                     <Card className="fluent-card">
                        <CardHeader>
                           <CardTitle>Notification Preferences</CardTitle>
                           <CardDescription>Manage how and when you receive system alerts.</CardDescription>
                        </CardHeader>
                        <CardContent className="min-h-[300px] flex flex-col items-center justify-center text-slate-500 dark:text-gray-500">
                           <Bell className="h-12 w-12 mb-4 opacity-20" />
                           <p>Notification settings coming soon</p>
                        </CardContent>
                     </Card>
                  </TabsContent>

                   {/* API GATEWAY */}
                   <TabsContent value="api" className="space-y-6 m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                      <div className="space-y-1 mb-6">
                         <h2 className="text-lg font-bold">API Gateway Configuration</h2>
                         <p className="text-sm text-slate-600 dark:text-gray-400">Manage API keys and connection usage.</p>
                      </div>
                      <ApiOverlayConfig />
                   </TabsContent>

                   {/* STORAGE */}
                   <TabsContent value="storage" className="m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                      <DatabaseSettings />
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

               </div>
            </Tabs>
         </div>
      </div>
    </div>
  );
}

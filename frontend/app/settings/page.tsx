'use client';

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { 
  Settings as SettingsIcon, Shield, Bell, Key, Save, 
  RotateCcw, Brain, Network, Monitor, Moon, Sun,
  Smartphone, Eye, Lock
} from "lucide-react";
import { ApiOverlayConfig } from "@/components/settings/ApiOverlayConfig";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("general");

  return (
    <div className="min-h-screen bg-black text-white font-sans selection:bg-blue-500/30">
       {/* Header */}
       <div className="border-b border-white/10 bg-gray-900/50 backdrop-blur-md sticky top-0 z-10">
          <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
             <div className="flex items-center gap-4">
                <div className="h-8 w-8 rounded bg-blue-600 flex items-center justify-center">
                   <SettingsIcon className="h-4 w-4 text-white" />
                </div>
                <div>
                   <h1 className="text-sm font-bold tracking-wide">System Configuration</h1>
                   <div className="text-[10px] text-gray-400 font-mono">Registry v2.4.9 • prod-us-east-1</div>
                </div>
             </div>
             <div className="flex gap-2">
                <Button variant="ghost" size="sm" className="h-8 text-xs text-gray-400 border border-white/10 hover:bg-white/5 hover:text-white gap-2">
                   <RotateCcw className="h-3 w-3" /> Revert
                </Button>
                <Button size="sm" className="h-8 text-xs bg-blue-600 hover:bg-blue-700 font-bold gap-2">
                   <Save className="h-3 w-3" /> Save Changes
                </Button>
             </div>
          </div>
       </div>

       <div className="max-w-6xl mx-auto px-6 py-8">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex gap-8">
             
             {/* Sidebar Navigation */}
             <div className="w-64 shrink-0 space-y-6">
                <div className="space-y-1">
                   {[
                      { id: 'general', icon: Monitor, label: 'Appearance' },
                      { id: 'notifications', icon: Bell, label: 'Notifications' },
                      { id: 'security', icon: Shield, label: 'Security & Auth' },
                      { id: 'api', icon: Key, label: 'API Gateway' },
                      { id: 'ai', icon: Brain, label: 'AI Models' },
                   ].map((item) => (
                      <button
                         key={item.id}
                         onClick={() => setActiveTab(item.id)}
                         className={`w-full flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg transition-all ${
                            activeTab === item.id 
                            ? 'bg-blue-600/10 text-blue-400 border border-blue-600/20' 
                            : 'text-gray-400 hover:text-white hover:bg-white/5'
                         }`}
                      >
                         <item.icon className="h-4 w-4" />
                         {item.label}
                      </button>
                   ))}
                </div>

                <div className="pt-6 border-t border-white/10">
                   <div className="text-[10px] font-bold text-gray-500 uppercase tracking-wider mb-2">System Status</div>
                   <div className="space-y-2">
                      <div className="flex justify-between text-xs text-gray-400">
                         <span>Gateway</span>
                         <span className="text-green-400">Online</span>
                      </div>
                      <div className="flex justify-between text-xs text-gray-400">
                         <span>Database</span>
                         <span className="text-green-400">Connected</span>
                      </div>
                      <div className="flex justify-between text-xs text-gray-400">
                         <span>Latency</span>
                         <span className="text-gray-300">24ms</span>
                      </div>
                   </div>
                </div>
             </div>

             {/* Content Area */}
             <div className="flex-1 space-y-6">
                
                {/* GENERAL / APPEARANCE */}
                <TabsContent value="general" className="space-y-6 m-0 focus-visible:ring-0">
                   <div className="space-y-1 mb-6">
                      <h2 className="text-lg font-bold">Appearance Settings</h2>
                      <p className="text-sm text-gray-400">Customize the interface density and theme preferences.</p>
                   </div>
                   
                   <Card className="bg-gray-900/30 border-white/10">
                      <CardHeader>
                         <CardTitle className="text-sm">Theme Preference</CardTitle>
                         <CardDescription className="text-gray-400 text-xs">Select your preferred interface mode.</CardDescription>
                      </CardHeader>
                      <CardContent className="grid grid-cols-3 gap-4">
                         <div className="border border-blue-500 bg-blue-900/20 p-4 rounded-lg flex flex-col items-center gap-2 cursor-pointer">
                            <Moon className="h-6 w-6 text-blue-400" />
                            <span className="text-xs font-bold text-blue-400">Dark (Default)</span>
                         </div>
                         <div className="border border-white/10 hover:bg-white/5 p-4 rounded-lg flex flex-col items-center gap-2 cursor-pointer opacity-50">
                            <Sun className="h-6 w-6 text-gray-400" />
                            <span className="text-xs font-bold text-gray-400">Light</span>
                         </div>
                         <div className="border border-white/10 hover:bg-white/5 p-4 rounded-lg flex flex-col items-center gap-2 cursor-pointer opacity-50">
                            <Monitor className="h-6 w-6 text-gray-400" />
                            <span className="text-xs font-bold text-gray-400">System</span>
                         </div>
                      </CardContent>
                   </Card>

                   <Card className="bg-gray-900/30 border-white/10">
                      <CardHeader>
                         <CardTitle className="text-sm">Interface Density</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-4">
                         <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                               <div className="text-sm font-medium">Compact Mode</div>
                               <div className="text-xs text-gray-500">Reduce padding and font size for higher data density.</div>
                            </div>
                            <Switch checked={true} />
                         </div>
                         <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                               <div className="text-sm font-medium">Show Technical ID's</div>
                               <div className="text-xs text-gray-500">Display UUIDs and raw identifiers in lists.</div>
                            </div>
                            <Switch />
                         </div>
                      </CardContent>
                   </Card>
                </TabsContent>

                {/* NOTIFICATIONS */}
                <TabsContent value="notifications" className="space-y-6 m-0 focus-visible:ring-0">
                   <div className="space-y-1 mb-6">
                      <h2 className="text-lg font-bold">Notification Preferences</h2>
                      <p className="text-sm text-gray-400">Manage how and when you receive system alerts.</p>
                   </div>
                    {/* ... Notification content placeholders ... */}
                    <div className="p-12 border border-dashed border-white/10 rounded-lg flex flex-col items-center justify-center text-gray-500">
                        <Bell className="h-8 w-8 mb-2 opacity-50" />
                        <span className="text-sm">Notification settings coming soon</span>
                    </div>
                </TabsContent>

                 {/* API GATEWAY (Using existing component) */}
                 <TabsContent value="api" className="space-y-6 m-0 focus-visible:ring-0">
                    <div className="space-y-1 mb-6">
                       <h2 className="text-lg font-bold">API Gateway Configuration</h2>
                       <p className="text-sm text-gray-400">Manage API keys and connection usage.</p>
                    </div>
                    <ApiOverlayConfig />
                 </TabsContent>

                 {/* Placeholder for others */}
                 <TabsContent value="security" className="m-0 focus-visible:ring-0">
                    <div className="p-12 border border-dashed border-white/10 rounded-lg flex flex-col items-center justify-center text-gray-500">
                        <Lock className="h-8 w-8 mb-2 opacity-50" />
                        <span className="text-sm">Security Hub Implementation Pending</span>
                    </div>
                 </TabsContent>

                 <TabsContent value="ai" className="m-0 focus-visible:ring-0">
                    <div className="p-12 border border-dashed border-white/10 rounded-lg flex flex-col items-center justify-center text-gray-500">
                        <Brain className="h-8 w-8 mb-2 opacity-50" />
                        <span className="text-sm">AI Model Controls Pending</span>
                    </div>
                 </TabsContent>

             </div>
          </Tabs>
       </div>
    </div>
  );
}

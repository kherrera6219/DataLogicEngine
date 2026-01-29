'use client';

import React, { useState } from 'react';
import { Button } from "@/components/ui/button";

import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { 
  Settings as SettingsIcon, Shield, Bell, Save, 
  Brain, Network, Monitor, Sun, Lock
} from "lucide-react";
import { ApiOverlayConfig } from "@/components/settings/ApiOverlayConfig";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { AppSidebar } from "@/components/layout/AppSidebar";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("general");

  return (
    <div className="flex h-screen bg-[#111111] text-white font-sans overflow-hidden">
      
      {/* Global Sidebar */}
      <AppSidebar />

      <div className="flex-1 flex flex-col overflow-y-auto bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">
         
         {/* Acrylic Header */}
         <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center justify-between px-8 backdrop-blur-3xl">
            <h1 className="text-title font-bold text-gray-100 flex items-center gap-3">
               <SettingsIcon className="h-5 w-5 text-gray-400" />
               Settings 
               <span className="text-sm font-normal text-gray-500">/ Configuration</span>
            </h1>
            <Button className="bg-blue-600 hover:bg-blue-700 font-bold shadow-lg shadow-blue-900/20">
               <Save className="h-4 w-4 mr-2" /> Save Changes
            </Button>
         </div>

         <div className="max-w-[1600px] w-full mx-auto p-8 space-y-8 animate-connected-enter">
            
            <Tabs value={activeTab} onValueChange={setActiveTab} className="flex gap-8 items-start">
               
               {/* Settings Sidebar */}
               <div className="w-64 shrink-0 space-y-6 sticky top-24">
                  <TabsList className="flex flex-col h-auto bg-transparent space-y-1 p-0">
                     {[
                        { id: 'general', label: 'General', icon: Monitor },
                        { id: 'notifications', label: 'Notifications', icon: Bell },
                        { id: 'api', label: 'API Gateway', icon: Network },
                        { id: 'security', label: 'Security', icon: Shield },
                        { id: 'ai', label: 'AI Models', icon: Brain },
                     ].map(tab => (
                        <TabsTrigger 
                           key={tab.id} 
                           value={tab.id}
                           className="w-full justify-start px-4 py-3 h-auto text-sm font-medium data-[state=active]:bg-blue-600 data-[state=active]:text-white data-[state=active]:shadow-lg hover:bg-white/5 rounded-xl transition-all"
                        >
                           <tab.icon className="h-4 w-4 mr-3" />
                           {tab.label}
                        </TabsTrigger>
                     ))}
                  </TabsList>

                  <Card className="fluent-card bg-gradient-to-br from-purple-900/20 to-blue-900/20 border-blue-500/20">
                     <CardContent className="p-4 space-y-3">
                        <div className="flex items-center gap-2 text-blue-400 font-semibold text-sm">
                           <Shield className="h-4 w-4" /> Enterprise Protected
                        </div>
                        <p className="text-xs text-gray-400">Settings are enforced by global registry policies.</p>
                     </CardContent>
                  </Card>
               </div>

               {/* Content Area */}
               <div className="flex-1 space-y-6 min-w-0">
                  
                  {/* GENERAL SETTINGS */}
                  <TabsContent value="general" className="space-y-6 m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                     <Card className="fluent-card bg-[#1a1a1a] border-[#333]">
                        <CardHeader>
                           <CardTitle>Appearance</CardTitle>
                           <CardDescription>Customize the interface look and feel.</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                           <div className="flex items-center justify-between p-4 rounded-xl bg-black/20 border border-white/5">
                              <div className="flex items-center gap-4">
                                 <div className="h-10 w-10 rounded-full bg-white/5 flex items-center justify-center">
                                    <Sun className="h-5 w-5 text-yellow-400" />
                                 </div>
                                 <div>
                                    <div className="font-medium text-gray-200">Theme Preference</div>
                                    <div className="text-xs text-gray-500">Select your preferred system theme</div>
                                 </div>
                              </div>
                              <div className="flex gap-2">
                                 <Button variant="outline" size="sm" className="bg-blue-600/20 border-blue-500/50 text-blue-400">Dark</Button>
                                 <Button variant="ghost" size="sm" className="text-gray-500">Light</Button>
                              </div>
                           </div>
                        </CardContent>
                     </Card>
                  </TabsContent>

                  {/* NOTIFICATIONS */}
                  <TabsContent value="notifications" className="space-y-6 m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                     <Card className="fluent-card bg-[#1a1a1a] border-[#333]">
                        <CardHeader>
                           <CardTitle>Notification Preferences</CardTitle>
                           <CardDescription>Manage how and when you receive system alerts.</CardDescription>
                        </CardHeader>
                        <CardContent className="min-h-[300px] flex flex-col items-center justify-center text-gray-500">
                           <Bell className="h-12 w-12 mb-4 opacity-20" />
                           <p>Notification settings coming soon</p>
                        </CardContent>
                     </Card>
                  </TabsContent>

                   {/* API GATEWAY */}
                   <TabsContent value="api" className="space-y-6 m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                      <div className="space-y-1 mb-6">
                         <h2 className="text-lg font-bold">API Gateway Configuration</h2>
                         <p className="text-sm text-gray-400">Manage API keys and connection usage.</p>
                      </div>
                      <ApiOverlayConfig />
                   </TabsContent>

                   {/* SECURITY */}
                   <TabsContent value="security" className="m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                      <Card className="fluent-card bg-[#1a1a1a] border-[#333]">
                         <CardContent className="min-h-[300px] flex flex-col items-center justify-center text-gray-500">
                             <Lock className="h-12 w-12 mb-4 opacity-20" />
                             <p>Security Hub Implementation Pending</p>
                         </CardContent>
                      </Card>
                   </TabsContent>

                   {/* AI MODELS */}
                   <TabsContent value="ai" className="m-0 focus-visible:ring-0 animate-in fade-in slide-in-from-right-4 duration-500">
                      <Card className="fluent-card bg-[#1a1a1a] border-[#333]">
                         <CardContent className="min-h-[300px] flex flex-col items-center justify-center text-gray-500">
                             <Brain className="h-12 w-12 mb-4 opacity-20" />
                             <p>AI Model Controls Pending</p>
                         </CardContent>
                      </Card>
                   </TabsContent>

               </div>
            </Tabs>
         </div>
      </div>
    </div>
  );
}

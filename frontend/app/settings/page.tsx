'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Select } from "@/components/ui/select";
import { useToast } from "@/components/ui/use-toast";

import { PageLayout } from "@/components/ui/page-layout";
import { Settings as SettingsIcon, Shield, Bell, Key, Save, Trash2, RotateCcw, Brain } from "lucide-react";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("general");
  const [emailNotifs, setEmailNotifs] = useState(true);
  const [systemAlerts, setSystemAlerts] = useState(true);
  const { toast } = useToast();

  const handleSave = () => {
    toast("Configuration committed to UKG Registry.", "success", 3000);
  };

  return (
    <PageLayout
      title="Internal Controls"
      description="System-wide configuration and environmental preferences."
      breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "System Settings" }]}
      actions={
        <Button 
          variant="outline" 
          className="h-11 px-6 rounded-xl glass-morphism gap-2"
          onClick={() => setActiveTab("general")}
        >
          <RotateCcw className="h-4 w-4" /> Reset Defaults
        </Button>
      }
    >
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-8">
        <TabsList className="bg-white/5 border border-white/5 p-1 rounded-2xl h-12">
          <TabsTrigger value="general" className="rounded-xl px-6 data-[state=active]:bg-blue-600 data-[state=active]:text-white font-bold transition-all gap-2">
            <SettingsIcon className="h-4 w-4" /> General
          </TabsTrigger>
          <TabsTrigger value="security" className="rounded-xl px-6 data-[state=active]:bg-blue-600 data-[state=active]:text-white font-bold transition-all gap-2">
            <Shield className="h-4 w-4" /> Security
          </TabsTrigger>
          <TabsTrigger value="notifications" className="rounded-xl px-6 data-[state=active]:bg-blue-600 data-[state=active]:text-white font-bold transition-all gap-2">
            <Bell className="h-4 w-4" /> Alerts
          </TabsTrigger>
          <TabsTrigger value="ai" className="rounded-xl px-6 data-[state=active]:bg-blue-600 data-[state=active]:text-white font-bold transition-all gap-2">
            <Brain className="h-4 w-4" /> AI Controls
          </TabsTrigger>
          <TabsTrigger value="api" className="rounded-xl px-6 data-[state=active]:bg-blue-600 data-[state=active]:text-white font-bold transition-all gap-2">
            <Key className="h-4 w-4" /> API Access
          </TabsTrigger>
        </TabsList>

        <TabsContent value="general" className="animate-in fade-in slide-in-from-left-2 duration-300">
          <Card className="glass-card border-white/10 shadow-2xl">
            <CardHeader className="border-b border-white/5 mx-6 px-0 pb-6">
              <CardTitle className="text-xl font-bold">Registry Preferences</CardTitle>
              <CardDescription className="text-muted-foreground font-medium">Basic system settings and display preferences.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-8 pt-8">
              <div className="flex items-center justify-between group">
                <div className="space-y-0.5">
                  <div className="font-bold uppercase tracking-widest text-[10px]">Visual Theme</div>
                  <div className="text-xs text-muted-foreground">Select preferred interface luminosity standard.</div>
                </div>
                <Select defaultValue="dark" aria-label="Select system theme" className="w-[180px] bg-white/5 border-white/10 rounded-xl h-11 focus:ring-blue-500 font-semibold">
                  <option value="system">System Default</option>
                  <option value="light">Luminous Light</option>
                  <option value="dark">Deep Space Dark</option>
                </Select>
              </div>
              <div className="flex items-center justify-between group">
                <div className="space-y-0.5">
                  <div className="font-bold uppercase tracking-widest text-[10px]">Natural Language</div>
                  <div className="text-xs text-muted-foreground">Regional localization for the graph interface.</div>
                </div>
                <Select defaultValue="en" aria-label="Select interface language" className="w-[180px] bg-white/5 border-white/10 rounded-xl h-11 focus:ring-blue-500 font-semibold">
                  <option value="en">English (US)</option>
                  <option value="es">Castellano</option>
                  <option value="fr">Français</option>
                  <option value="de">Deutsch</option>
                </Select>
              </div>
            </CardContent>
            <CardFooter className="border-t border-white/5 mx-6 px-0 py-6">
              <Button className="h-11 px-8 rounded-xl bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/20 font-bold transition-all gap-2" onClick={handleSave}>
                <Save className="h-4 w-4" /> Commit Preferences
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>

        <TabsContent value="security" className="animate-in fade-in slide-in-from-left-2 duration-300">
          <Card className="glass-card border-white/10 shadow-2xl">
            <CardHeader className="border-b border-white/5 mx-6 px-0 pb-6">
              <CardTitle className="text-xl font-bold">Hardened Security</CardTitle>
              <CardDescription className="text-muted-foreground font-medium">Manage access tokens and rotation policies.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-8 pt-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-3">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest" htmlFor="new-password">New Security Token</label>
                  <Input id="new-password" type="password" className="bg-white/5 border-white/10 h-11 rounded-xl focus-visible:ring-blue-500" />
                </div>
                <div className="space-y-3">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest" htmlFor="confirm-password">Confirm Token Rotation</label>
                  <Input id="confirm-password" type="password" className="bg-white/5 border-white/10 h-11 rounded-xl focus-visible:ring-blue-500" />
                </div>
              </div>
              <div className="p-6 bg-blue-600/5 border border-blue-500/20 rounded-2xl">
                <div className="flex items-center justify-between group">
                  <div className="space-y-1">
                    <div className="font-bold text-blue-500 uppercase tracking-tighter flex items-center gap-2">
                      Multi-Factor Authentication Required
                    </div>
                    <div className="text-xs text-blue-100/60 font-medium">Establish a second vector of truth for identity verification.</div>
                  </div>
                  <Switch className="data-[state=checked]:bg-blue-600" aria-label="Toggle Multi-Factor Authentication" />
                </div>
              </div>
            </CardContent>
            <CardFooter className="border-t border-white/5 mx-6 px-0 py-6">
              <Button className="h-11 px-8 rounded-xl bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/20 font-bold transition-all gap-2" onClick={handleSave}>
                <Shield className="h-4 w-4" /> Rotate Authority Tokens
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="animate-in fade-in slide-in-from-left-2 duration-300">
          <Card className="glass-card border-white/10 shadow-2xl">
            <CardHeader className="border-b border-white/5 mx-6 px-0 pb-6">
              <CardTitle className="text-xl font-bold">Alert Configuration</CardTitle>
              <CardDescription className="text-muted-foreground font-medium">Control signal thresholds for critical alerts.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-0 pt-4 px-0">
              <div className="flex items-center justify-between p-6 hover:bg-white/5 transition-colors group">
                <div className="space-y-0.5">
                  <div className="font-bold uppercase tracking-widest text-[10px]">Email Summaries</div>
                  <div className="text-xs text-muted-foreground">Daily compliance audit and trace history exports.</div>
                </div>
                <Switch checked={emailNotifs} onCheckedChange={setEmailNotifs} className="data-[state=checked]:bg-blue-600" aria-label="Toggle email notifications" />
              </div>
              <div className="flex items-center justify-between p-6 hover:bg-white/5 transition-colors group border-t border-white/5">
                <div className="space-y-0.5">
                  <div className="font-bold uppercase tracking-widest text-[10px]">Real-time Probes</div>
                  <div className="text-xs text-muted-foreground">In-app Toast alerts for system level events.</div>
                </div>
                <Switch checked={systemAlerts} onCheckedChange={setSystemAlerts} className="data-[state=checked]:bg-blue-600" aria-label="Toggle system alerts" />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="ai" className="animate-in fade-in slide-in-from-left-2 duration-300">
          <Card className="glass-card border-white/10 shadow-2xl">
            <CardHeader className="border-b border-white/5 mx-6 px-0 pb-6">
              <CardTitle className="text-xl font-bold">AI Processing Controls</CardTitle>
              <CardDescription className="text-muted-foreground font-medium">Configure cloud provider preference and data handling.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-8 pt-8">
               <div className="flex items-center justify-between group">
                 <div className="space-y-0.5">
                   <div className="font-bold uppercase tracking-widest text-[10px] text-blue-500">Enable AI Processing</div>
                   <div className="text-xs text-muted-foreground">Master toggle for all LLM interactions. Disabling stops all cloud calls.</div>
                 </div>
                 <Switch defaultChecked aria-label="Toggle AI Processing" className="data-[state=checked]:bg-blue-600" />
               </div>

               <div className="flex items-center justify-between group">
                <div className="space-y-0.5">
                  <div className="font-bold uppercase tracking-widest text-[10px]">Preferred Provider</div>
                  <div className="text-xs text-muted-foreground">Select primary inference engine. Auto-failover enabled.</div>
                </div>
                <Select defaultValue="auto" aria-label="Select AI provider" className="w-[180px] bg-white/5 border-white/10 rounded-xl h-11 focus:ring-blue-500 font-semibold">
                  <option value="auto">Auto (Recommended)</option>
                  <option value="openai">OpenAI (GPT-4o)</option>
                  <option value="azure">Azure OpenAI</option>
                  <option value="anthropic">Anthropic Claude</option>
                  <option value="google">Vertex AI</option>
                </Select>
              </div>

              <div className="p-6 bg-red-500/5 border border-red-500/20 rounded-2xl">
                 <div className="flex items-center justify-between group">
                   <div className="space-y-1">
                     <div className="font-bold text-red-500 uppercase tracking-tighter flex items-center gap-2">
                       Store AI Conversation History
                     </div>
                     <div className="text-xs text-red-100/60 font-medium">Allow system to persist prompts for context memory.</div>
                   </div>
                   <Switch defaultChecked className="data-[state=checked]:bg-red-600" aria-label="Toggle History Storage" />
                 </div>
              </div>
            </CardContent>
            <CardFooter className="border-t border-white/5 mx-6 px-0 py-6">
              <Button className="h-11 px-8 rounded-xl bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/20 font-bold transition-all gap-2" onClick={handleSave}>
                <Save className="h-4 w-4" /> Save AI Preferences
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>

        <TabsContent value="api" className="animate-in fade-in slide-in-from-left-2 duration-300">
          <Card className="glass-card border-white/10 shadow-2xl">
            <CardHeader className="border-b border-white/5 mx-6 px-0 pb-6">
              <CardTitle className="text-xl font-bold">API Access Control</CardTitle>
              <CardDescription className="text-muted-foreground font-medium">Manage Identity Proof Tokens for CLI and SDK access.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-8">
              {[
                { key: "dle_sk_****************29a", label: "Production Node 01" },
                { key: "dle_sk_****************8b2", label: "CI/CD Pipeline Tracer" }
              ].map((token) => (
                <div key={token.key} className="p-4 bg-white/5 border border-white/5 rounded-2xl flex justify-between items-center group">
                  <div className="space-y-1">
                    <div className="font-bold text-blue-500 uppercase tracking-widest text-[9px]">{token.label}</div>
                    <code className="text-xs font-mono text-gray-400">{token.key}</code>
                  </div>
                  <Button size="icon" variant="ghost" className="h-9 w-9 rounded-xl text-red-500 hover:text-red-400 hover:bg-red-500/10 transition-all" aria-label={`Revoke token: ${token.label}`}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </CardContent>
            <CardFooter className="border-t border-white/5 mx-6 px-0 py-6">
              <Button className="h-11 px-8 rounded-xl bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-500/20 font-bold transition-all gap-2" onClick={() => toast("Generating new API token...", "info")}>
                <Key className="h-4 w-4" /> Provision New Token
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </PageLayout>
  );
}

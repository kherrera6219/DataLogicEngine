'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Select } from "@/components/ui/select";

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("general");
  const [emailNotifs, setEmailNotifs] = useState(true);
  const [systemAlerts, setSystemAlerts] = useState(true);

  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8">
      <div className="container mx-auto max-w-5xl">
         <header className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
            <p className="text-gray-500">System configuration and preferences.</p>
         </header>

         <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-8">
               <TabsTrigger value="general">General</TabsTrigger>
               <TabsTrigger value="security">Security</TabsTrigger>
               <TabsTrigger value="notifications">Notifications</TabsTrigger>
               <TabsTrigger value="api">API Access</TabsTrigger>
            </TabsList>

            <TabsContent value="general">
               <Card>
                  <CardHeader>
                     <CardTitle>General Configuration</CardTitle>
                     <CardDescription>Basic system settings and display preferences.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                     <div className="flex items-center justify-between">
                        <div>
                           <div className="font-medium">Theme</div>
                           <div className="text-sm text-gray-500">Select system theme preference.</div>
                        </div>
                        <Select className="w-[180px]">
                           <option>System Default</option>
                           <option>Light</option>
                           <option>Dark</option>
                        </Select>
                     </div>
                     <div className="flex items-center justify-between">
                        <div>
                           <div className="font-medium">Language</div>
                           <div className="text-sm text-gray-500">Dashboard interface language.</div>
                        </div>
                        <Select className="w-[180px]">
                           <option>English (US)</option>
                           <option>Spanish</option>
                           <option>French</option>
                           <option>German</option>
                        </Select>
                     </div>
                  </CardContent>
                  <CardFooter>
                     <Button>Save Preferences</Button>
                  </CardFooter>
               </Card>
            </TabsContent>

            <TabsContent value="security">
               <Card>
                  <CardHeader>
                     <CardTitle>Security Settings</CardTitle>
                     <CardDescription>Manage password and authentication methods.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                     <div className="space-y-4">
                        <div className="space-y-2">
                           <label className="text-sm font-medium">New Password</label>
                           <Input type="password" />
                        </div>
                        <div className="space-y-2">
                           <label className="text-sm font-medium">Confirm New Password</label>
                           <Input type="password" />
                        </div>
                     </div>
                     <div className="border-t pt-4">
                         <div className="flex items-center justify-between">
                             <div>
                                <div className="font-medium">Two-Factor Authentication</div>
                                <div className="text-sm text-gray-500">Add an extra layer of security.</div>
                             </div>
                             <Switch />
                         </div>
                     </div>
                  </CardContent>
                  <CardFooter>
                     <Button>Update Security</Button>
                  </CardFooter>
               </Card>
            </TabsContent>

            <TabsContent value="notifications">
               <Card>
                  <CardHeader>
                     <CardTitle>Notification Preferences</CardTitle>
                     <CardDescription>Control how and when you receive alerts.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                      <div className="flex items-center justify-between">
                         <div>
                            <div className="font-medium">Email Notifications</div>
                            <div className="text-sm text-gray-500">Receive daily summaries and critical alerts.</div>
                         </div>
                         <Switch checked={emailNotifs} onCheckedChange={setEmailNotifs} />
                      </div>
                      <div className="flex items-center justify-between">
                         <div>
                            <div className="font-medium">System Alerts</div>
                            <div className="text-sm text-gray-500">In-app notifications for system events.</div>
                         </div>
                         <Switch checked={systemAlerts} onCheckedChange={setSystemAlerts} />
                      </div>
                  </CardContent>
               </Card>
            </TabsContent>

            <TabsContent value="api">
               <Card>
                  <CardHeader>
                     <CardTitle>API Configuration</CardTitle>
                     <CardDescription>Manage your Personal Access Tokens.</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                      <div className="p-4 bg-gray-100 dark:bg-gray-900 rounded-lg flex justify-between items-center">
                          <code className="text-sm font-mono">dle_sk_****************29a</code>
                          <Button size="sm" variant="outline">Revoke</Button>
                      </div>
                      <div className="p-4 bg-gray-100 dark:bg-gray-900 rounded-lg flex justify-between items-center">
                          <code className="text-sm font-mono">dle_sk_****************8b2</code>
                          <Button size="sm" variant="outline">Revoke</Button>
                      </div>
                  </CardContent>
                  <CardFooter>
                     <Button>Generate New Key</Button>
                  </CardFooter>
               </Card>
            </TabsContent>
         </Tabs>
      </div>
    </main>
  );
}

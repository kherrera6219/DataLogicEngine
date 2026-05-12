'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Download, Trash2, AlertTriangle, CheckCircle, FileJson, Activity } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/use-toast';
import { buildApiUrl, request } from '@/lib/api';

import { PageLayout } from "@/components/ui/page-layout";

export default function PrivacySettingsPage() {
  const { user, logout } = useAuth();
  const { toast } = useToast();
  const [isExporting, setIsExporting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  const handleExport = async () => {
    setIsExporting(true);
    setMessage(null);
    try {
      const response = await fetch(buildApiUrl('/user/data/export'), {
        credentials: 'include',
      });
      if (!response.ok) throw new Error('Export failed');
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ukg_data_export_${user?.username || 'user'}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      
      setMessage({ type: 'success', text: 'Data export started successfully.' });
    } catch {
      setMessage({ type: 'error', text: 'Failed to export data. Please try again later.' });
    } finally {
      setIsExporting(false);
    }
  };

  const handleDelete = async () => {
    if (!confirm('CRITICAL ACTION: This will permanently delete your local profile and all simulation history on this machine. This cannot be undone. Proceed?')) {
      return;
    }

    setIsDeleting(true);
    setMessage(null);
    try {
      const data = await request<{ success?: boolean; error?: string; message?: string }>('/user/data/delete', {
        method: 'POST',
        body: JSON.stringify({ confirm: 'DELETE' }),
      });
      
      if (data?.success !== false) {
        toast('Your data has been deleted. You will now be logged out.', 'success');
        setTimeout(() => logout(), 2000);
      } else {
        throw new Error(data.error || data.message || 'Deletion failed');
      }
    } catch {
      setMessage({ type: 'error', text: 'Failed to delete profile. Please contact support.' });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <PageLayout
      title="Privacy & Data Management"
      description="Manage your local information and exercise your data rights."
      breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Settings", href: "/settings" }, { label: "Privacy" }]}
    >

      {message && (
        <Alert variant={message.type === 'success' ? 'default' : 'destructive'} className={message.type === 'success' ? 'border-green-500/50 bg-green-500/10' : ''}>
          {message.type === 'success' ? <CheckCircle className="h-4 w-4" /> : <AlertTriangle className="h-4 w-4" />}
          <AlertTitle>{message.type === 'success' ? 'Success' : 'Error'}</AlertTitle>
          <AlertDescription>{message.text}</AlertDescription>
        </Alert>
      )}

      <div className="grid gap-6">
        {/* Data Portability */}
        <Card className="border-premium bg-background/50">
          <CardHeader>
            <CardTitle>Data Portability</CardTitle>
            <CardDescription>Download a copy of all information stored in your local DataLogicEngine instance.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-4 p-4 rounded-xl bg-muted/50 border border-border">
              <FileJson className="h-10 w-10 text-blue-500 shrink-0" />
              <div className="space-y-1">
                <p className="font-bold text-sm">JSON Format Export</p>
                <p className="text-xs text-muted-foreground">
                  Includes your profile, simulation results, and local configurations. This file can be used to migrate your data or for personal auditing.
                </p>
              </div>
            </div>
            <Button 
              onClick={handleExport} 
              disabled={isExporting}
              className="w-full sm:w-auto gap-2"
            >
              {isExporting ? 'Preparing Export...' : <><Download className="h-4 w-4" /> Export My Data</>}
            </Button>
          </CardContent>
        </Card>

        {/* Right to Erase */}
        <Card className="border-red-500/20 bg-red-500/5">
          <CardHeader>
            <CardTitle className="text-red-500">Danger Zone</CardTitle>
            <CardDescription>Permanently erase your information from this system.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert variant="destructive" className="bg-transparent border-red-500/20">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>This action is non-reversible</AlertTitle>
              <AlertDescription>
                Deleting your profile will remove all locally stored simulation traces and knowledge indices associated with your Windows SID.
              </AlertDescription>
            </Alert>
            <Button 
              variant="destructive" 
              onClick={handleDelete}
              disabled={isDeleting}
              className="gap-2"
            >
              <Trash2 className="h-4 w-4" /> 
              {isDeleting ? 'Deleting...' : 'Delete My Account & Data'}
            </Button>
          </CardContent>
        </Card>
      </div>

        {/* Background Activity Disclosure */}
        <Card className="border-premium bg-background/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-muted-foreground" />
              Background Activity
            </CardTitle>
            <CardDescription>What this application does when you are not actively using it.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <ul className="space-y-2">
              <li className="flex items-start gap-2">
                <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-green-500 shrink-0 mt-2" />
                <span><strong className="text-foreground">Health checks</strong> — The app periodically pings <code className="text-xs bg-muted px-1 rounded">/api/health</code> to display the gateway status indicator. No user data is sent.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-green-500 shrink-0 mt-2" />
                <span><strong className="text-foreground">WebSocket keep-alives</strong> — An open WebSocket connection is maintained to receive real-time trace updates. The connection sends only a session token; no query content is transmitted in the background.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-yellow-500 shrink-0 mt-2" />
                <span><strong className="text-foreground">Session refresh</strong> — Your authentication session is silently refreshed before it expires to avoid unexpected logouts. This contacts the backend server only.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="mt-0.5 h-1.5 w-1.5 rounded-full bg-muted-foreground shrink-0 mt-2" />
                <span><strong className="text-foreground">No telemetry or analytics</strong> — DataLogicEngine does not run any third-party analytics, crash reporters, or ad networks in the background.</span>
              </li>
            </ul>
            <p className="pt-2 text-xs border-t border-border">
              All background activity stops when the application is closed. For questions about cloud data handling, see the{' '}
              <Link href="/about/cloud-services" className="text-blue-500 hover:underline">Cloud Services</Link> page.
            </p>
          </CardContent>
        </Card>

      <footer className="text-center pt-8 border-t border-border">
        <p className="text-xs text-muted-foreground">
          DataLogicEngine complies with MS-P1 Privacy Standards.
          <br />
          For cloud-specific data queries, please refer to our <Link href="/about/cloud-services" className="text-blue-500 hover:underline">Cloud Disclosure</Link>.
        </p>
      </footer>
    </PageLayout>
  );
}

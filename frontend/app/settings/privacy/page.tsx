'use client';

import React, { useState } from 'react';
import { Shield, Download, Trash2, AlertTriangle, CheckCircle, FileJson } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/use-toast';

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
      const response = await fetch('/api/v1/user/data/export');
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
      const response = await fetch('/api/v1/user/data/delete', { method: 'POST' });
      const data = await response.json();
      
      if (data.success) {
        toast('Your data has been deleted. You will now be logged out.', 'success');
        setTimeout(() => logout(), 2000);
      } else {
        throw new Error(data.error || 'Deletion failed');
      }
    } catch {
      setMessage({ type: 'error', text: 'Failed to delete profile. Please contact support.' });
      setIsDeleting(false);
    }
  };

  return (
    <div className="container mx-auto py-10 px-4 max-w-4xl space-y-8">
      <header className="space-y-2">
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
          <Shield className="text-blue-500 h-8 w-8" />
          Privacy & Data Management
        </h1>
        <p className="text-muted-foreground">
          Manage your local information and exercise your data rights.
        </p>
      </header>

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

      <footer className="text-center pt-8 border-t border-border">
        <p className="text-xs text-muted-foreground">
          DataLogicEngine complies with MS-P1 Privacy Standards. 
          <br />
          For cloud-specific data queries, please refer to our <a href="/about/cloud-services" className="text-blue-500 hover:underline">Cloud Disclosure</a>.
        </p>
      </footer>
    </div>
  );
}

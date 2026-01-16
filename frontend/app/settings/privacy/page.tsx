
'use client';

import { useState } from 'react';
import { Download, Trash2, AlertTriangle, FileText, CheckCircle, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useAuth } from '@/contexts/AuthContext';

export default function PrivacySettingsPage() {
  const [isExporting, setIsExporting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const { toast } = useToast();
  const { user, logout } = useAuth();

  const handleExport = async (format: 'json' | 'csv') => {
    try {
      setIsExporting(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/v1/user/data/export?format=${format}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) throw new Error('Export failed');

      // Trigger download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `datalogic_export_${user?.username || 'user'}_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      toast({
        title: "Export Started",
        description: "Your data has been successfully exported.",
      });
    } catch (error) {
      toast({
        title: "Export Failed",
        description: "Could not retrieve your data. Please try again.",
        variant: "destructive"
      });
    } finally {
      setIsExporting(false);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      setIsDeleting(true);
      const token = localStorage.getItem('token');
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/v1/user/data/delete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ confirmation: user?.username })
      });

      const data = await response.json();
      if (!response.ok) throw new Error(data.error || 'Deletion failed');

      toast({
        title: "Account Scheduled for Deletion",
        description: "You will be logged out now. Your data will be permanently removed in 30 days.",
      });

      // Wait a moment then logout
      setTimeout(() => logout(), 2000);

    } catch (error) {
      toast({
        title: "Deletion Failed",
        description: String(error),
        variant: "destructive"
      });
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="container max-w-4xl py-8 space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Privacy & Data Rights</h1>
        <p className="text-muted-foreground mt-2">
          Manage your personal data, export your history, or request account deletion in compliance with GDPR and CCPA.
        </p>
      </div>

      <div className="grid gap-6">
        {/* Data Collections */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Shield className="h-5 w-5 text-blue-500" />
              <CardTitle>Data We Collect</CardTitle>
            </div>
            <CardDescription>Transparency about the information stored in your account.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
             <div className="grid gap-4 md:grid-cols-2">
                <div className="flex items-start gap-3 p-3 rounded-lg border bg-secondary/20">
                   <div className="p-2 bg-blue-500/10 rounded-md text-blue-500"><FileText className="h-4 w-4"/></div>
                   <div>
                      <p className="font-medium text-sm">Account Profile</p>
                      <p className="text-xs text-muted-foreground">Username, email, preferences</p>
                   </div>
                </div>
                <div className="flex items-start gap-3 p-3 rounded-lg border bg-secondary/20">
                   <div className="p-2 bg-purple-500/10 rounded-md text-purple-500"><FileText className="h-4 w-4"/></div>
                   <div>
                      <p className="font-medium text-sm">Chat History</p>
                      <p className="text-xs text-muted-foreground">Questions and AI responses</p>
                   </div>
                </div>
                 <div className="flex items-start gap-3 p-3 rounded-lg border bg-secondary/20">
                   <div className="p-2 bg-amber-500/10 rounded-md text-amber-500"><FileText className="h-4 w-4"/></div>
                   <div>
                      <p className="font-medium text-sm">Technical Traces</p>
                      <p className="text-xs text-muted-foreground">Execution logs for debugging</p>
                   </div>
                </div>
                <div className="flex items-start gap-3 p-3 rounded-lg border bg-secondary/20">
                   <div className="p-2 bg-green-500/10 rounded-md text-green-500"><FileText className="h-4 w-4"/></div>
                   <div>
                      <p className="font-medium text-sm">Audit Logs</p>
                      <p className="text-xs text-muted-foreground">Security and access records</p>
                   </div>
                </div>
             </div>
          </CardContent>
        </Card>

        {/* Export Data */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <Download className="h-5 w-5 text-green-500" />
              <CardTitle>Export Your Data</CardTitle>
            </div>
            <CardDescription>Download a copy of all data associated with your account.</CardDescription>
          </CardHeader>
          <CardContent>
             <div className="flex flex-col sm:flex-row gap-4">
               <Button onClick={() => handleExport('json')} disabled={isExporting} variant="outline" className="w-full sm:w-auto">
                 {isExporting ? "Exporting..." : "Download JSON Archive"}
               </Button>
               {/* CSV Future Implementation 
               <Button onClick={() => handleExport('csv')} disabled={isExporting} variant="outline" className="w-full sm:w-auto">
                 Download CSV
               </Button>
               */}
             </div>
             <p className="text-xs text-muted-foreground mt-4 flex items-center gap-2">
               <CheckCircle className="h-3 w-3" />
               Includes all chat sessions, profile settings, and activity logs.
             </p>
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="border-red-500/20 bg-red-500/5">
          <CardHeader>
            <div className="flex items-center gap-2 text-red-500">
              <AlertTriangle className="h-5 w-5" />
              <CardTitle>Danger Zone</CardTitle>
            </div>
            <CardDescription className="text-red-500/80">Permanent actions that cannot be undone immediately.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <p className="font-medium text-sm text-foreground">Delete Account</p>
                <p className="text-xs text-muted-foreground">
                  Permanently remove your account and all associated data.
                </p>
              </div>
              
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button variant="destructive" size="sm">
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Account
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                    <AlertDialogDescription>
                      This action cannot be undone immediately. Your data will be scheduled for permanent deletion in <b>30 days</b>.
                      During this grace period, you may contact support to restore your account.
                      <br /><br />
                      To confirm, please verify this is your account: <b>{user?.username}</b>
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction onClick={handleDeleteAccount} className="bg-red-500 hover:bg-red-600">
                      Yes, Delete My Account
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

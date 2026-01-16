'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import useSWR from 'swr';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, Download, ShieldCheck, FileText } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function ComplianceDashboard() {
  const router = useRouter();
  const [exporting, setExporting] = useState(false);
  const [days, setDays] = useState(30);

  // Fetch standards (just to show dashboard is alive)
  const { data: standards, error } = useSWR('compliance.standards', () => api.compliance.standards());
  
  const handleExport = async () => {
    try {
      setExporting(true);
      await api.compliance.exportAuditLogs(days);
    } catch (e) {
      console.error('Export failed', e);
      alert('Failed to trigger export.');
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="container mx-auto p-8 space-y-8">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
           <h1 className="text-3xl font-bold tracking-tight">Compliance Dashboard</h1>
           <p className="text-muted-foreground">Manage centralized security policies and audit trails.</p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Audit Export Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              <CardTitle>Audit Logs</CardTitle>
            </div>
            <CardDescription>
              Export system-wide audit trails for SIEM integration or compliance review.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
               <div className="flex flex-col gap-1">
                 <label className="text-sm font-medium">Time Range</label>
                 <select 
                   className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                   value={days}
                   onChange={(e) => setDays(Number(e.target.value))}
                 >
                   <option value={7}>Last 7 Days</option>
                   <option value={30}>Last 30 Days</option>
                   <option value={90}>Last 90 Days</option>
                   <option value={365}>Last 1 Year</option>
                 </select>
               </div>
               <div className="flex-1 flex items-end">
                 <Button className="w-full" onClick={handleExport} disabled={exporting}>
                   {exporting ? 'Exporting...' : (
                      <>
                        <Download className="mr-2 h-4 w-4" />
                        Export to CSV
                      </>
                   )}
                 </Button>
               </div>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Exports include: User Logins, Data Access, System Changes, and API Usage.
            </p>
          </CardContent>
        </Card>

        {/* Standards Status (Planned) */}
        <Card>
          <CardHeader>
             <div className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-green-600" />
                <CardTitle>Active Standards</CardTitle>
             </div>
             <CardDescription>
                Live monitoring of compliance frameworks.
             </CardDescription>
          </CardHeader>
          <CardContent>
             {error ? (
                <div className="p-4 rounded-md bg-destructive/10 text-destructive text-sm">
                   Could not load standards data.
                </div>
             ) : !standards ? (
                <div className="text-sm text-muted-foreground">Loading compliance data...</div>
             ) : (
                 <div className="space-y-2">
                    {(standards as Record<string, unknown>[]) && (standards as Record<string, unknown>[]).length > 0 ? (
                        (standards as Record<string, unknown>[]).map((child: Record<string, unknown>) => (
                            <div key={(child.uid as string) || Math.random()} className="flex justify-between items-center p-2 rounded-md border">
                               <span className="font-medium">{(child.name || child.id) as string}</span>
                               <Badge variant="outline">Active</Badge>
                            </div>
                        ))
                    ) : (
                        <div className="text-sm text-muted-foreground">No active standards configured.</div>
                    )}
                 </div>
             )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

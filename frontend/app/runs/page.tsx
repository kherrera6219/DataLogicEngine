'use client';

import { useState, useEffect } from 'react';
import Link from "next/link";
import { api, TraceRun } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";

export default function TraceRunsPage() {
  const [runs, setRuns] = useState<TraceRun[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
     let mounted = true;
     api.trace.list(20).then(data => {
        if (mounted) {
           setRuns((data || []) as TraceRun[]);
           setIsLoading(false);
        }
     }).catch(() => {
        if (mounted) setIsLoading(false);
     });
     return () => { mounted = false; };
  }, []);

  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8">
      <div className="container mx-auto max-w-7xl">
         <header className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Trace Explorer</h1>
            <p className="text-gray-500">Detailed execution logs of Knowledge Algorithms.</p>
         </header>

         <Card>
            <CardHeader>
               <CardTitle>Recent Execution Runs</CardTitle>
            </CardHeader>
            <CardContent>
               <Table>
                  <TableHeader>
                     <TableRow>
                        <TableHead>Run ID</TableHead>
                        <TableHead>Algorithm (KA)</TableHead>
                        <TableHead>Start Time</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Action</TableHead>
                     </TableRow>
                  </TableHeader>
                  <TableBody>
                     {isLoading && (
                        <TableRow>
                           <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                              Loading traces...
                           </TableCell>
                        </TableRow>
                     )}
                     {!isLoading && runs.length === 0 && (
                        <TableRow>
                           <TableCell colSpan={5} className="text-center py-8 text-gray-500">
                              No traces found.
                           </TableCell>
                        </TableRow>
                     )}
                     {runs.map((run) => (
                        <TableRow key={run.run_id}>
                           <TableCell className="font-mono text-xs">{run.run_id.substring(0,8)}</TableCell>
                           <TableCell>{run.ka_id || 'N/A'}</TableCell>
                           <TableCell className="text-gray-500">{new Date(run.created_at).toLocaleString()}</TableCell>
                           <TableCell>
                              <Badge variant={run.status === 'completed' ? 'success' : run.status === 'failed' ? 'destructive' : 'secondary'}>
                                 {run.status}
                              </Badge>
                           </TableCell>
                           <TableCell className="text-right">
                              <Link href={`/runs/view?id=${run.run_id}`}>
                                 <Button size="sm" variant="outline">View Trace</Button>
                              </Link>
                           </TableCell>
                        </TableRow>
                     ))}
                  </TableBody>
               </Table>
            </CardContent>
         </Card>
      </div>
    </main>
  );
}

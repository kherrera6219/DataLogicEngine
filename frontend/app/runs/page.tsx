'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function TraceRunsPage() {
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
                        <TableHead>Duration</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Steps</TableHead>
                        <TableHead className="text-right">Action</TableHead>
                     </TableRow>
                  </TableHeader>
                  <TableBody>
                     {[
                        { id: "TR-2819", ka: "KA-001 (AoT)", start: "2024-03-12 10:42:01", dur: "1.2s", status: "Completed", steps: 12 },
                        { id: "TR-2818", ka: "KA-042 (Causal)", start: "2024-03-12 10:41:45", dur: "0.8s", status: "Completed", steps: 8 },
                        { id: "TR-2817", ka: "KA-114 (Fractal)", start: "2024-03-12 10:40:12", dur: "4.5s", status: "Failed", steps: 4 },
                     ].map((run) => (
                        <TableRow key={run.id}>
                           <TableCell className="font-mono text-xs">{run.id}</TableCell>
                           <TableCell>{run.ka}</TableCell>
                           <TableCell className="text-gray-500">{run.start}</TableCell>
                           <TableCell>{run.dur}</TableCell>
                           <TableCell>
                              <Badge variant={run.status === 'Completed' ? 'success' : 'destructive'}>{run.status}</Badge>
                           </TableCell>
                           <TableCell>{run.steps}</TableCell>
                           <TableCell className="text-right">
                              <Link href={`/runs/${run.id}`}>
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

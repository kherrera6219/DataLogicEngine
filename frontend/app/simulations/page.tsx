'use client';

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

const simulations = [
  { id: "SIM-001", name: "Global Supply Chain Stress Test", type: "Chaos", status: "Running", progress: 85, created: "2024-03-10" },
  { id: "SIM-002", name: "GDPR Compliance Audit - Healthcare", type: "Compliance", status: "Completed", progress: 100, created: "2024-03-09" },
  { id: "SIM-003", name: "Tech Sector Bubble Analysis", type: "Economics", status: "Failed", progress: 42, created: "2024-03-08" },
  { id: "SIM-004", name: "Cybersecurity Red Team Alpha", type: "Security", status: "Running", progress: 12, created: "2024-03-11" },
  { id: "SIM-005", name: "Carbon Tax Impact Model", type: "Policy", status: "Queued", progress: 0, created: "2024-03-12" },
];

export default function SimulationsPage() {
  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-8">
      <div className="container mx-auto max-w-7xl">
        <header className="mb-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Simulation Monitor</h1>
            <p className="text-gray-500">Track and control active reasoning simulations and agent swarms.</p>
          </div>
          <Button variant="default" size="lg">
             New Simulation
          </Button>
        </header>

        <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 shadow-sm overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Progress</TableHead>
                <TableHead>Created</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {simulations.map((sim) => (
                <TableRow key={sim.id}>
                  <TableCell className="font-mono text-xs">{sim.id}</TableCell>
                  <TableCell className="font-medium">{sim.name}</TableCell>
                  <TableCell>{sim.type}</TableCell>
                  <TableCell>
                    <Badge variant={
                        sim.status === 'Completed' ? 'success' :
                        sim.status === 'Running' ? 'default' :
                        sim.status === 'Failed' ? 'destructive' : 'secondary'
                    }>
                        {sim.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700 w-24">
                      <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${sim.progress}%` }}></div>
                    </div>
                  </TableCell>
                  <TableCell className="text-gray-500">{sim.created}</TableCell>
                  <TableCell className="text-right">
                    <Button variant="ghost" size="sm">Details</Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </main>
  );
}

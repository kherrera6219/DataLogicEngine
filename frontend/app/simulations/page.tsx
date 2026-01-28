'use client';

import { useState, useEffect } from 'react';
import useSWR from 'swr';
import { api } from "@/lib/api";
import { useSocket, SimulationProgress } from "@/lib/socket";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { PlayCircle, Plus, RefreshCw, Wifi, WifiOff } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function SimulationsPage() {
  const { data: simulations, isLoading, mutate } = useSWR('simulations-list', api.simulation.list);
  const [isCreating, setIsCreating] = useState(false);
  const [liveProgress, setLiveProgress] = useState<Record<string, SimulationProgress>>({});
  const [isConnected, setIsConnected] = useState(false);

  // WebSocket connection for real-time updates
  const socket = useSocket({
    onConnected: () => setIsConnected(true),
    onDisconnected: () => setIsConnected(false),
    onSimulationProgress: (data) => {
      setLiveProgress(prev => ({ ...prev, [data.simulation_id]: data }));
    },
    onSimulationComplete: (data) => {
      setLiveProgress(prev => {
        const updated = { ...prev };
        delete updated[data.simulation_id];
        return updated;
      });
      mutate(); // Refresh list when simulation completes
    }
  });

  // Subscribe to active simulations
  useEffect(() => {
    if (simulations && socket.isConnected) {
      simulations
        .filter(sim => sim.status === 'active')
        .forEach(sim => socket.subscribeToSimulation(sim.uid));
    }
  }, [simulations, socket, socket.isConnected]);

  const handleCreate = async () => {
    setIsCreating(true);
    try {
        await api.simulation.create(`Simulation ${new Date().toLocaleString()}`, { mode: 'standard' });
        mutate();
        } catch {
            console.error("Failed to run simulation");
        } finally {
        setIsCreating(false);
    }
  };

  const handleStep = async (uid: string) => {
      await api.simulation.step(uid);
      mutate();
  };

  return (
    <main className="min-h-screen bg-muted/40 p-8">
      <div className="container mx-auto max-w-7xl space-y-8">
        <header className="flex justify-between items-center">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <h1 className="text-3xl font-bold tracking-tight">Simulation Monitor</h1>
              {isConnected ? (
                <Badge variant="outline" className="gap-1 text-green-600 border-green-600">
                  <Wifi className="h-3 w-3" /> Live
                </Badge>
              ) : (
                <Badge variant="outline" className="gap-1 text-gray-400">
                  <WifiOff className="h-3 w-3" /> Offline
                </Badge>
              )}
            </div>
            <p className="text-muted-foreground">Track and control active reasoning simulations and agent swarms.</p>
          </div>
          <Button onClick={handleCreate} disabled={isCreating} className="gap-2">
             {isCreating ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
             New Simulation
          </Button>
        </header>

        <Card>
          <CardHeader>
             <CardTitle>Active Sessions</CardTitle>
             <CardDescription>Real-time view of running simulation instances.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
                <TableHeader>
                <TableRow>
                    <TableHead>UID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Steps</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                </TableRow>
                </TableHeader>
                <TableBody>
                {isLoading && Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i}>
                        <TableCell><Skeleton className="h-4 w-24" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-48" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-16" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-12" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                        <TableCell><Skeleton className="h-8 w-8 ml-auto" /></TableCell>
                    </TableRow>
                ))}

                {!isLoading && simulations?.length === 0 && (
                    <TableRow>
                        <TableCell colSpan={6} className="text-center py-12 text-muted-foreground">
                            No active simulations. Create one to begin.
                        </TableCell>
                    </TableRow>
                )}

                {simulations?.map((sim) => (
                    <TableRow key={sim.uid}>
                    <TableCell className="font-mono text-xs">{sim.uid.substring(0,8)}...</TableCell>
                    <TableCell className="font-medium">{sim.name}</TableCell>
                    <TableCell>
                        <Badge variant={
                            sim.status === 'completed' ? 'default' :
                            sim.status === 'active' ? 'secondary' : 'destructive'
                        }>
                            {sim.status}
                        </Badge>
                    </TableCell>
                    <TableCell>
                      {liveProgress[sim.uid] ? (
                        <span className="text-blue-600 font-medium animate-pulse">
                          {liveProgress[sim.uid].step}/{liveProgress[sim.uid].total_steps}
                        </span>
                      ) : (
                        sim.current_step
                      )}
                    </TableCell>
                    <TableCell className="text-muted-foreground text-sm">
                        {new Date(sim.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                        <Button 
                            variant="ghost" 
                            size="icon" 
                            onClick={() => handleStep(sim.uid)}
                            disabled={sim.status !== 'active'}
                            title="Run Step"
                        >
                            <PlayCircle className="h-4 w-4" />
                        </Button>
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

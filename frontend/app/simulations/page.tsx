'use client';

import { useState, useEffect } from 'react';
import useSWR from 'swr';
import { api } from "@/lib/api";
import { useSocket, SimulationProgress } from "@/lib/socket";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { PlayCircle, Plus, RefreshCw, WifiOff } from "lucide-react";
import { cn } from "@/lib/utils";
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
    <main className="min-h-screen bg-transparent p-8 text-white">
      <div className="container mx-auto max-w-7xl space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <header className="flex justify-between items-center mb-12">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent">
                Simulation Monitor
              </h1>
              {isConnected ? (
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-medium shadow-[0_0_15px_rgba(34,197,94,0.1)]">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.8)]"></span>
                  Live Connection
                </div>
              ) : (
                <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-gray-400 text-xs font-medium">
                  <WifiOff className="h-3 w-3" /> Offline
                </div>
              )}
            </div>
            <p className="text-gray-400 max-w-2xl text-sm leading-relaxed">
              Track and control active reasoning simulations and agent swarms through the UKG Enterprise validation framework.
            </p>
          </div>
          <Button 
            onClick={handleCreate} 
            disabled={isCreating} 
            className="gap-2 bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20 transition-all hover:scale-105 active:scale-95"
          >
             {isCreating ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
             New Simulation
          </Button>
        </header>

        <Card className="fluent-acrylic border-white/10 overflow-hidden shadow-2xl">
          <CardHeader className="border-b border-white/5 bg-white/5">
             <div className="flex items-center justify-between">
               <div>
                  <CardTitle className="text-gray-100 text-lg">Active Sessions</CardTitle>
                  <CardDescription className="text-gray-500">Real-time view of running simulation instances.</CardDescription>
               </div>
               <div className="flex gap-2 text-[10px] font-mono text-gray-600">
                  <span>SYSTEM_UPTIME: 99.9%</span>
                  <span>•</span>
                  <span>LOAD_AVG: 0.12</span>
               </div>
             </div>
          </CardHeader>
          <CardContent className="p-0">
            <Table>
                <TableHeader className="bg-white/5">
                <TableRow className="hover:bg-transparent border-white/5">
                    <TableHead className="text-gray-400 font-bold text-xs uppercase tracking-wider">UID</TableHead>
                    <TableHead className="text-gray-400 font-bold text-xs uppercase tracking-wider">Name</TableHead>
                    <TableHead className="text-gray-400 font-bold text-xs uppercase tracking-wider">Status</TableHead>
                    <TableHead className="text-gray-400 font-bold text-xs uppercase tracking-wider">Steps</TableHead>
                    <TableHead className="text-gray-400 font-bold text-xs uppercase tracking-wider">Created</TableHead>
                    <TableHead className="text-right text-gray-400 font-bold text-xs uppercase tracking-wider">Actions</TableHead>
                </TableRow>
                </TableHeader>
                <TableBody>
                {isLoading && Array.from({ length: 3 }).map((_, i) => (
                    <TableRow key={i} className="border-white/5">
                        <TableCell><Skeleton className="h-4 w-24 bg-white/5" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-48 bg-white/5" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-16 bg-white/5" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-12 bg-white/5" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-32 bg-white/5" /></TableCell>
                        <TableCell><Skeleton className="h-8 w-8 ml-auto bg-white/5" /></TableCell>
                    </TableRow>
                ))}

                {!isLoading && simulations?.length === 0 && (
                    <TableRow className="hover:bg-transparent">
                        <TableCell colSpan={6} className="text-center py-24 text-gray-500">
                            <div className="flex flex-col items-center gap-3">
                              <RefreshCw className="h-8 w-8 text-white/10" />
                              <p>No active simulations. Create one to begin data synthesis.</p>
                            </div>
                        </TableCell>
                    </TableRow>
                )}

                {simulations?.map((sim) => (
                    <TableRow key={sim.uid} className="border-white/5 hover:bg-white/5 group transition-colors">
                    <TableCell className="font-mono text-[10px] text-gray-500">{sim.uid}</TableCell>
                    <TableCell className="font-medium text-gray-100">{sim.name}</TableCell>
                    <TableCell>
                        <Badge 
                          className={cn(
                            "px-2 py-0 h-5 text-[10px] font-bold border-none",
                            sim.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                            sim.status === 'active' ? 'bg-blue-500/20 text-blue-400 animate-pulse' : 'bg-red-500/20 text-red-400'
                          )}
                        >
                            {sim.status.toUpperCase()}
                        </Badge>
                    </TableCell>
                    <TableCell className="font-mono">
                          {liveProgress[sim.uid] ? (() => {
                            const progress = Math.round((liveProgress[sim.uid].step / liveProgress[sim.uid].total_steps) * 100);
                            return (
                              <div className="flex flex-col gap-1">
                                <span className="text-blue-400 text-xs font-bold">
                                  {liveProgress[sim.uid].step}/{liveProgress[sim.uid].total_steps}
                                </span>
                                <div className="w-16 h-1 bg-white/5 rounded-full overflow-hidden">
                                  <div 
                                    className={`h-full bg-blue-500 transition-all duration-500 ${
                                      progress >= 75 ? 'w-full' : 
                                      progress >= 50 ? 'w-3/4' : 
                                      progress >= 25 ? 'w-1/2' : 'w-1/4'
                                    }`}
                                  />
                                </div>
                              </div>
                            );
                          })() : (
                        <span className="text-gray-400">{sim.current_step}</span>
                      )}
                    </TableCell>
                    <TableCell className="text-gray-500 text-xs">
                        {new Date(sim.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                        <Button 
                            variant="ghost" 
                            size="icon" 
                            onClick={() => handleStep(sim.uid)}
                            disabled={sim.status !== 'active'}
                            className="h-8 w-8 text-gray-400 hover:text-white hover:bg-white/10 rounded-lg transition-all opacity-0 group-hover:opacity-100"
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

        {/* System Diagnostics Footer */}
        <div className="flex justify-between items-center text-[10px] text-gray-600 font-mono pt-4 border-t border-white/5">
           <div className="flex gap-4">
              <span>UKG_OS_v2.5</span>
              <span>SIM_ENGINE_BRIDGE: CONNECTED</span>
           </div>
           <div className="flex gap-4">
              <span>LATENCY: 12ms</span>
              <span>LOAD: OPTIMAL</span>
           </div>
        </div>
      </div>
    </main>
  );
}

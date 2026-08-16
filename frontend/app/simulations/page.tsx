'use client';

import { useState, useEffect } from 'react';
import useSWR from 'swr';
import { api } from "@/lib/api";
import { useSocket, SimulationProgress } from "@/lib/socket";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { PauseCircle, PlayCircle, Plus, RefreshCw, RotateCcw, Square, WifiOff } from "lucide-react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { SimulationPreflight } from "@/lib/api/types";

export default function SimulationsPage() {
  const { data: simulations, isLoading, error, mutate } = useSWR(
    'simulations-list',
    api.simulation.list,
    { refreshInterval: 3000 },
  );
  const [isCreating, setIsCreating] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [simulationName, setSimulationName] = useState('');
  const [simulationQuery, setSimulationQuery] = useState('');
  const [simulationDepth, setSimulationDepth] = useState<'quick' | 'standard' | 'deep'>('standard');
  const [executionMode, setExecutionMode] = useState<'live' | 'fixed_seed_local'>('live');
  const [simulationSeed, setSimulationSeed] = useState(0);
  const [preflight, setPreflight] = useState<SimulationPreflight | null>(null);
  const [operationError, setOperationError] = useState<string | null>(null);
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

  // Subscribe to active simulations whenever the list or connection state changes
  useEffect(() => {
    if (simulations && isConnected) {
      simulations
        .filter(sim => ['queued', 'running', 'materialization_pending'].includes(sim.status))
        .forEach(sim => socket.subscribeToSimulation(sim.session_id));
    }
  }, [simulations, isConnected, socket]);

  const scenarioParameters = () => ({
    query: simulationQuery.trim(),
    depth: simulationDepth,
    execution_mode: executionMode,
    seed: simulationSeed,
  });

  const handlePreflight = async () => {
    const query = simulationQuery.trim();
    if (!query) {
      setOperationError('Enter a scenario to simulate.');
      return;
    }
    setIsCreating(true);
    setOperationError(null);
    try {
        const result = await api.simulation.preflight(scenarioParameters());
        setPreflight(result);
        return result;
    } catch (err) {
        setOperationError(err instanceof Error ? err.message : 'Simulation preflight failed');
        return null;
    } finally {
        setIsCreating(false);
    }
  };

  const handleCreate = async () => {
    if (!simulationQuery.trim()) {
      setOperationError('Enter a scenario to simulate.');
      return;
    }
    setIsCreating(true);
    setOperationError(null);
    try {
        const checked = preflight || await api.simulation.preflight(scenarioParameters());
        setPreflight(checked);
        if (checked.budget.admissible === false) {
          throw new Error(`Simulation cannot run: ${checked.budget.blocking_code || 'preflight blocked'}`);
        }
        await api.simulation.create(
          simulationName.trim() || `Simulation ${new Date().toLocaleString()}`,
          scenarioParameters()
        );
        setSimulationName('');
        setSimulationQuery('');
        setPreflight(null);
        setIsCreateOpen(false);
        mutate();
        } catch (err) {
            setOperationError(err instanceof Error ? err.message : 'Failed to create simulation');
        } finally {
        setIsCreating(false);
    }
  };

  const handleRun = async (sessionId: string) => {
      setOperationError(null);
      try {
        await api.simulation.run(sessionId);
        mutate();
      } catch (err) {
        setOperationError(err instanceof Error ? err.message : 'Failed to run simulation');
      }
  };

  const handleControl = async (
    sessionId: string,
    action: 'pause' | 'resume' | 'retry' | 'cancel',
  ) => {
    setOperationError(null);
    try {
      await api.simulation[action](sessionId);
      await mutate();
    } catch (err) {
      setOperationError(err instanceof Error ? err.message : `Failed to ${action} simulation`);
    }
  };

  const totalSimulations = simulations?.length || 0;
  const activeSimulations = simulations?.filter((sim) => ['queued', 'running', 'paused', 'materialization_pending'].includes(sim.status)).length || 0;
  const completedSimulations = simulations?.filter((sim) => sim.status === 'completed').length || 0;

  return (
    <div className="min-h-full bg-background text-foreground font-sans">
      <div className="min-h-full bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">

        {/* Acrylic Header */}
        <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center justify-between px-8 backdrop-blur-3xl">
          <div className="flex items-center gap-3">
            <div className="bg-blue-500/10 p-2 rounded-lg border border-blue-500/20">
              <PlayCircle className="h-5 w-5 text-blue-400" />
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-title font-bold text-slate-900 dark:text-gray-100">Simulation Monitor</h1>
                {isConnected ? (
                  <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-medium">
                    <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse shadow-[0_0_8px_rgba(34,197,94,0.8)]"></span>
                    Live
                  </div>
                ) : (
                  <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-slate-600 dark:text-gray-400 text-xs font-medium">
                    <WifiOff className="h-3 w-3" /> Offline
                  </div>
                )}
              </div>
              <div className="text-[10px] text-slate-500 dark:text-gray-500 font-mono uppercase tracking-widest">UKG Enterprise Validation Framework</div>
            </div>
          </div>
          <Button
            onClick={() => { setOperationError(null); setIsCreateOpen(true); }}
            disabled={isCreating}
            className="gap-2 bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-900/20 transition-all hover:scale-105 active:scale-95"
          >
            <Plus className="h-4 w-4" />
            New Simulation
          </Button>
        </div>

        <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New Simulation</DialogTitle>
              <DialogDescription>Define the scenario for the bounded multi-agent simulation workflow.</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <label htmlFor="simulation-name" className="text-sm font-medium">Name</label>
                <Input
                  id="simulation-name"
                  value={simulationName}
                  onChange={(event) => setSimulationName(event.target.value)}
                  placeholder="Optional simulation name"
                  maxLength={255}
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="simulation-query" className="text-sm font-medium">Scenario</label>
                <textarea
                  id="simulation-query"
                  value={simulationQuery}
                  onChange={(event) => { setSimulationQuery(event.target.value); setPreflight(null); }}
                  placeholder="Enter the question or scenario to evaluate"
                  maxLength={5000}
                  rows={6}
                  className="flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />
              </div>
              <div className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-xs text-muted-foreground" data-testid="simulation-bounds-note">
                Bounded simulation only (contract <span className="font-mono">dle-simulation.v1</span>).
                Depth caps provider work: quick / standard / deep. Not available on the chat gateway path —
                use this page, not Governed Chat.
              </div>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                <div className="space-y-2">
                  <label htmlFor="simulation-depth" className="text-sm font-medium">Depth</label>
                  <Select
                    id="simulation-depth"
                    value={simulationDepth}
                    onChange={(event) => { setSimulationDepth(event.target.value as typeof simulationDepth); setPreflight(null); }}
                  >
                    <option value="quick">Quick (lower call budget)</option>
                    <option value="standard">Standard</option>
                    <option value="deep">Deep (higher call budget)</option>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label htmlFor="simulation-mode" className="text-sm font-medium">Execution</label>
                  <Select
                    id="simulation-mode"
                    value={executionMode}
                    onChange={(event) => { setExecutionMode(event.target.value as typeof executionMode); setPreflight(null); }}
                  >
                    <option value="live">Live provider</option>
                    <option value="fixed_seed_local">Fixed-seed qualification</option>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label htmlFor="simulation-seed" className="text-sm font-medium">Seed</label>
                  <Input
                    id="simulation-seed"
                    type="number"
                    min={0}
                    max={2147483647}
                    value={simulationSeed}
                    onChange={(event) => { setSimulationSeed(Number(event.target.value) || 0); setPreflight(null); }}
                  />
                </div>
              </div>
              {preflight && (
                <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-4 text-sm" data-testid="simulation-preflight">
                  <div className="font-semibold">Preflight passed</div>
                  <div className="mt-2 grid grid-cols-2 gap-2 text-muted-foreground">
                    <span>Provider calls: {preflight.plan.max_provider_calls}</span>
                    <span>Token ceiling: {preflight.budget.max_total_tokens.toLocaleString()}</span>
                    <span>Tool calls: {preflight.budget.max_tool_calls ?? 0}</span>
                    <span>
                      Estimated cost: {preflight.budget.estimated_cost_usd == null ? 'Unavailable — pricing not approved' : `$${preflight.budget.estimated_cost_usd.toFixed(4)}`}
                    </span>
                    <span>Provider: {preflight.budget.provider_status ?? 'unknown'}</span>
                    <span>Admission: {preflight.budget.admissible === false ? preflight.budget.blocking_code : 'ready'}</span>
                  </div>
                  <div className="mt-2 break-all font-mono text-[10px] text-muted-foreground">
                    Scenario revision: {preflight.scenario_revision}
                  </div>
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsCreateOpen(false)} disabled={isCreating}>Cancel</Button>
              <Button variant="outline" onClick={() => void handlePreflight()} disabled={isCreating || !simulationQuery.trim()}>
                {isCreating ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : null}
                Preflight
              </Button>
              <Button onClick={() => void handleCreate()} disabled={isCreating || !simulationQuery.trim()}>
                {isCreating ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
                Create
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

      <div className="max-w-[1600px] w-full mx-auto p-8 space-y-8 animate-connected-enter">

        {(error || operationError) && (
          <Card className="border-red-500/30 bg-red-500/10" role="alert">
            <CardContent className="p-4 text-sm text-red-600 dark:text-red-300">
              {operationError || (error instanceof Error ? error.message : 'Simulation service is unavailable')}
            </CardContent>
          </Card>
        )}

        <Card className="fluent-acrylic border-white/10 overflow-hidden shadow-2xl">
          <CardHeader className="border-b border-white/5 bg-white/5">
             <div className="flex items-center justify-between">
               <div>
                  <CardTitle className="text-slate-900 dark:text-gray-100 text-lg">Active Sessions</CardTitle>
                  <CardDescription className="text-slate-600 dark:text-gray-500">Durable simulation sessions and live progress when execution is available.</CardDescription>
               </div>
               <div className="flex gap-2 text-[10px] font-mono text-gray-600">
                  <span>ACTIVE: {activeSimulations}</span>
                  <span>•</span>
                  <span>TOTAL: {totalSimulations}</span>
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

                {!isLoading && !error && simulations?.length === 0 && (
                    <TableRow className="hover:bg-transparent">
                        <TableCell colSpan={6} className="text-center py-24 text-gray-500">
                            <div className="flex flex-col items-center gap-3">
                              <RefreshCw className="h-8 w-8 text-slate-300 dark:text-white/10" />
                              <p>No active simulations. Create one to begin data synthesis.</p>
                            </div>
                        </TableCell>
                    </TableRow>
                )}

                {simulations?.map((sim) => (
                    <TableRow key={sim.session_id} className="border-white/5 hover:bg-white/5 group transition-colors">
                    <TableCell className="font-mono text-[10px] text-gray-500">{sim.session_id}</TableCell>
                    <TableCell className="font-medium text-slate-900 dark:text-gray-100">
                      <div>{sim.name || 'Untitled simulation'}</div>
                      {sim.results?.final_conclusion && (
                        <div className="mt-1 max-w-md truncate text-xs font-normal text-gray-500" title={sim.results.final_conclusion}>
                          {sim.results.final_conclusion}
                        </div>
                      )}
                      {sim.results?.validation?.status && (
                        <div className="mt-1 text-[10px] font-mono uppercase text-gray-500">
                          Confidence: {sim.results.confidence_score == null ? 'Not measured' : `${Math.round(sim.results.confidence_score * 100)}%`} · {sim.results.validation.status}
                        </div>
                      )}
                    </TableCell>
                    <TableCell>
                        <Badge 
                          className={cn(
                            "px-2 py-0 h-5 text-[10px] font-bold border-none",
                            sim.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                            ['queued', 'running'].includes(sim.status) ? 'bg-blue-500/20 text-blue-400 animate-pulse' :
                            sim.status === 'paused' ? 'bg-amber-500/20 text-amber-400' :
                            sim.status === 'materialization_pending' ? 'bg-purple-500/20 text-purple-400' :
                            sim.status === 'draft' ? 'bg-slate-500/20 text-slate-400' : 'bg-red-500/20 text-red-400'
                          )}
                        >
                            {sim.status.toUpperCase()}
                        </Badge>
                    </TableCell>
                    <TableCell className="font-mono">
                          {liveProgress[sim.session_id] ? (() => {
                            const current = liveProgress[sim.session_id].current_step;
                            const total = Math.max(1, liveProgress[sim.session_id].total_steps);
                            const progress = Math.round((current / total) * 100);
                            return (
                              <div className="flex flex-col gap-1">
                                <span className="text-blue-400 text-xs font-bold">
                                  {current}/{total}
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
                        <span className="text-gray-400">{sim.current_step}/{sim.plan?.max_provider_calls ?? sim.total_steps ?? '—'}</span>
                      )}
                    </TableCell>
                    <TableCell className="text-gray-500 text-xs">
                        {new Date(sim.created_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1 opacity-70 transition-opacity group-hover:opacity-100">
                        {sim.status === 'draft' && (
                          <Button aria-label="Run simulation" variant="ghost" size="icon" onClick={() => void handleRun(sim.session_id)} className="h-8 w-8">
                            <PlayCircle className="h-4 w-4" />
                          </Button>
                        )}
                        {['queued', 'running'].includes(sim.status) && (
                          <Button aria-label="Pause simulation" variant="ghost" size="icon" onClick={() => void handleControl(sim.session_id, 'pause')} className="h-8 w-8">
                            <PauseCircle className="h-4 w-4" />
                          </Button>
                        )}
                        {sim.status === 'paused' && (
                          <Button aria-label="Resume simulation" variant="ghost" size="icon" onClick={() => void handleControl(sim.session_id, 'resume')} className="h-8 w-8">
                            <PlayCircle className="h-4 w-4" />
                          </Button>
                        )}
                        {sim.status === 'failed' && (
                          <Button aria-label="Retry simulation" variant="ghost" size="icon" onClick={() => void handleControl(sim.session_id, 'retry')} className="h-8 w-8">
                            <RotateCcw className="h-4 w-4" />
                          </Button>
                        )}
                        {['draft', 'queued', 'running', 'paused'].includes(sim.status) && (
                          <Button aria-label="Cancel simulation" variant="ghost" size="icon" onClick={() => void handleControl(sim.session_id, 'cancel')} className="h-8 w-8 text-red-400">
                            <Square className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                    </TableRow>
                ))}
                </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* System Diagnostics Footer */}
        <div className="flex justify-between items-center text-[10px] text-slate-500 dark:text-gray-600 font-mono pt-4 border-t border-white/5">
           <div className="flex gap-4">
              <span>TOTAL_SIMULATIONS: {totalSimulations}</span>
              <span>COMPLETED: {completedSimulations}</span>
           </div>
           <div className="flex gap-4">
              <span>SOCKET: {isConnected ? 'CONNECTED' : 'OFFLINE'}</span>
              <span>LAST_REFRESH: {new Date().toLocaleTimeString()}</span>
           </div>
        </div>
      </div>
      </div>
    </div>
  );
}

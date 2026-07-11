'use client';

import { useState, useEffect, useRef } from 'react';
import { mcp, MCPStats } from '@/lib/api/mcp';
import { request } from '@/lib/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Server, Activity, Database, Terminal, Settings, Send, X } from 'lucide-react';
import Link from 'next/link';

export default function MCPDashboard() {
  const [stats, setStats] = useState<MCPStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  // MCP Console state
  const [consoleOpen, setConsoleOpen] = useState(false);
  const [consoleInput, setConsoleInput] = useState('');
  const [consoleLog, setConsoleLog] = useState<Array<{ type: 'cmd' | 'res' | 'err'; text: string }>>([]);
  const [consoleSending, setConsoleSending] = useState(false);
  const consoleEndRef = useRef<HTMLDivElement>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await mcp.getStats();
      setStats(data);
    } catch (err) {
      setError('Failed to load MCP stats');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    async function init() {
      await fetchStats();
      if (cancelled) return;
    }
    void init();
    return () => { cancelled = true; };
  }, []);

  const handleConsoleSend = async () => {
    const cmd = consoleInput.trim();
    if (!cmd) return;
    setConsoleLog((prev) => [...prev, { type: 'cmd', text: `> ${cmd}` }]);
    setConsoleInput('');
    setConsoleSending(true);
    try {
      // Send to MCP JSON-RPC endpoint
      const result = await request<unknown>('/mcp/console', {
        method: 'POST',
        body: JSON.stringify({ command: cmd }),
      });
      setConsoleLog((prev) => [...prev, { type: 'res', text: JSON.stringify(result, null, 2) }]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setConsoleLog((prev) => [...prev, { type: 'err', text: `Error: ${msg}` }]);
    } finally {
      setConsoleSending(false);
      setTimeout(() => consoleEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-muted-foreground">Loading MCP System...</div>;
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-500">
        <p>{error}</p>
        <Button onClick={fetchStats} variant="outline" className="mt-4">Retry</Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">MCP System</h1>
          <p className="text-muted-foreground">Model Context Protocol Management</p>
        </div>
        <div className="flex gap-2">
            <Link href="/admin/mcp/servers">
                <Button>
                    <Server className="w-4 h-4 mr-2" />
                    Manage Servers
                </Button>
            </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Servers</CardTitle>
            <Server className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active_servers || 0} / {stats?.total_servers || 0}</div>
            <p className="text-xs text-muted-foreground">
              Running instances
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Resources</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_resources || 0}</div>
            <p className="text-xs text-muted-foreground">
              Exposed data points
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tools</CardTitle>
            <Settings className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_tools || 0}</div>
            <p className="text-xs text-muted-foreground">
              Callable functions
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Connections</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.active_connections || 0}</div>
            <p className="text-xs text-muted-foreground">
              Active client sessions
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
        <Card>
            <CardHeader>
                <CardTitle>System Health</CardTitle>
            </CardHeader>
            <CardContent>
                <div className="space-y-2">
                    <div className="flex justify-between items-center text-sm">
                        <span>Status</span>
                        <span className={stats ? "text-green-500 font-medium" : "text-amber-500 font-medium"}>
                          {stats ? 'Stats available' : 'Unavailable'}
                        </span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                        <span>Health source</span>
                        <span>MCP statistics API</span>
                    </div>
                    <div className="flex justify-between items-center text-sm">
                        <span>Environment</span>
                        <span>{process.env.NODE_ENV}</span>
                    </div>
                </div>
            </CardContent>
        </Card>

        <Card>
            <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-2">
                 <Link href="/admin/mcp/servers">
                    <Button variant="outline" className="w-full justify-start">
                        <Server className="mr-2 h-4 w-4" />
                        View Server Registry
                    </Button>
                </Link>
                <Button
                  variant="outline"
                  className="w-full justify-start"
                  onClick={() => setConsoleOpen((o) => !o)}
                >
                    <Terminal className="mr-2 h-4 w-4" />
                    {consoleOpen ? 'Close MCP Console' : 'Open MCP Console'}
                </Button>
            </CardContent>
        </Card>
      </div>

      {/* MCP Console Panel */}
      {consoleOpen && (
        <Card className="border-green-500/30 bg-black text-green-400">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <CardTitle className="text-sm font-mono text-green-400 flex items-center gap-2">
              <Terminal className="h-4 w-4" /> MCP Console
            </CardTitle>
            <Button size="icon" variant="ghost" onClick={() => setConsoleOpen(false)} className="text-green-400 hover:text-white">
              <X className="h-4 w-4" />
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="h-48 overflow-y-auto font-mono text-xs space-y-1 bg-black/50 rounded p-3 border border-green-900/40">
              {consoleLog.length === 0 && (
                <p className="text-green-700">MCP Console ready. Type a command and press Enter.</p>
              )}
              {consoleLog.map((entry, i) => (
                <p key={i} className={entry.type === 'cmd' ? 'text-green-300' : entry.type === 'err' ? 'text-red-400' : 'text-green-500 whitespace-pre-wrap'}>
                  {entry.text}
                </p>
              ))}
              <div ref={consoleEndRef} />
            </div>
            <div className="flex gap-2">
              <Input
                className="font-mono text-sm bg-black border-green-700 text-green-300 focus-visible:ring-green-500"
                placeholder="Enter command..."
                value={consoleInput}
                onChange={(e) => setConsoleInput(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') void handleConsoleSend(); }}
                disabled={consoleSending}
              />
              <Button onClick={handleConsoleSend} disabled={consoleSending || !consoleInput.trim()} className="bg-green-700 hover:bg-green-600">
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

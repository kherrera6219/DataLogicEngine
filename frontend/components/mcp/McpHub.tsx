'use client';

import React, { useEffect, useState } from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Server, Settings, Zap, RefreshCw } from "lucide-react";
import { useRouter } from 'next/navigation';
import { request } from '@/lib/api';

interface MCPStatsRecord {
  total_servers?: number;
  active_servers?: number;
  total_tools?: number;
  active_connections?: number;
}

export function McpHub() {
  const router = useRouter();
  const [stats, setStats] = useState<MCPStatsRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadStats = React.useCallback(async () => {
    setError(null);
    try {
      const data = await request<{ stats?: MCPStatsRecord }>('/mcp/stats');
      setStats(data.stats || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load MCP stats');
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadStats();
  }, [loadStats]);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <section className="grid grid-cols-1 gap-4">
        <Card className="glass-card border-white/10 bg-gradient-to-r from-gray-900 to-black p-6">
          <div className="flex flex-col md:flex-row justify-between items-center text-center md:text-left gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-3 justify-center md:justify-start">
                <Zap className="h-6 w-6 text-yellow-400" />
                UKG Model Context Protocol (MCP) Hub
              </h1>
              <p className="text-muted-foreground mt-1">
                Live connectivity inventory for MCP servers and tools.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant="outline" className="bg-white/5 border-white/10 text-gray-400">Live API</Badge>
              <Button variant="outline" size="sm" onClick={() => void loadStats()} disabled={loading}>
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>
          </div>
        </Card>
      </section>

      {error && (
        <Card className="border-red-500/30 bg-red-500/10">
          <CardContent className="p-4 text-sm text-red-300">{error}</CardContent>
        </Card>
      )}

      <section>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: 'Total Servers', value: stats?.total_servers ?? 0, color: 'text-white' },
            { label: 'Active Servers', value: stats?.active_servers ?? 0, color: 'text-white' },
            { label: 'Total Tools', value: stats?.total_tools ?? 0, color: 'text-white' },
            { label: 'Connections', value: stats?.active_connections ?? 0, color: 'text-green-400' },
          ].map((stat) => (
            <Card key={stat.label} className="bg-white/5 border-white/10 text-center py-4">
              <div className="text-xs text-gray-400 uppercase tracking-widest mb-1">{stat.label}</div>
              <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
            </Card>
          ))}
        </div>
      </section>

      <section>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="hover:bg-white/5 transition-colors border-white/10 cursor-pointer group" onClick={() => router.push('/mcp?tab=server')}>
            <CardContent className="pt-6 flex flex-col items-center text-center space-y-4">
              <div className="p-4 rounded-full bg-blue-500/10 group-hover:bg-blue-500/20 transition-colors">
                <Server className="h-8 w-8 text-blue-400" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Configure MCP Servers</h3>
                <p className="text-sm text-gray-400 mt-2">Inspect server status, tools, resources, and prompts from live endpoints.</p>
              </div>
              <Button variant="outline" className="w-full border-white/10 hover:bg-white/10" onClick={(e) => { e.stopPropagation(); router.push('/mcp?tab=server'); }}>
                Manage Servers <ExternalLink className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:bg-white/5 transition-colors border-white/10 cursor-pointer group" onClick={() => router.push('/mcp?tab=client')}>
            <CardContent className="pt-6 flex flex-col items-center text-center space-y-4">
              <div className="p-4 rounded-full bg-purple-500/10 group-hover:bg-purple-500/20 transition-colors">
                <Zap className="h-8 w-8 text-purple-400" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Connect MCP Clients</h3>
                <p className="text-sm text-gray-400 mt-2">Create or remove server connections and search tool coverage.</p>
              </div>
              <Button variant="outline" className="w-full border-white/10 hover:bg-white/10" onClick={(e) => { e.stopPropagation(); router.push('/mcp?tab=client'); }}>
                Connect Clients <ExternalLink className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>

          <Card className="hover:bg-white/5 transition-colors border-white/10 cursor-pointer group" onClick={() => router.push('/mcp?tab=analytics')}>
            <CardContent className="pt-6 flex flex-col items-center text-center space-y-4">
              <div className="p-4 rounded-full bg-green-500/10 group-hover:bg-green-500/20 transition-colors">
                <Settings className="h-8 w-8 text-green-400" />
              </div>
              <div>
                <h3 className="text-lg font-bold text-white">Analyze MCP Traffic</h3>
                <p className="text-sm text-gray-400 mt-2">Review runtime trends, top tools, and server health telemetry.</p>
              </div>
              <Button variant="outline" className="w-full border-white/10 hover:bg-white/10" onClick={(e) => { e.stopPropagation(); router.push('/mcp?tab=analytics'); }}>
                Open Analytics <ExternalLink className="ml-2 h-4 w-4" />
              </Button>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}

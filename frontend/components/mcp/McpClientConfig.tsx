'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import {
  Plus, Search, Server, Settings, Trash2, RefreshCw,
  Globe, CheckCircle
} from "lucide-react";
import { request } from '@/lib/api';

interface MCPServerRecord {
  id: number;
  server_id: string;
  name: string;
  version: string;
  description: string;
  status: 'active' | 'inactive' | 'error';
}

interface MCPToolRecord {
  id: number;
  name: string;
  description: string;
  server_id: number;
  stats?: {
    execution_count?: number;
    success_count?: number;
    failure_count?: number;
  };
}

interface MCPStatsRecord {
  total_servers?: number;
  active_servers?: number;
  total_tools?: number;
  total_resources?: number;
  active_connections?: number;
}

interface ToolWithServer extends MCPToolRecord {
  serverName: string;
}

export function McpClientConfig() {
  const [isAddServerOpen, setIsAddServerOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [servers, setServers] = useState<MCPServerRecord[]>([]);
  const [tools, setTools] = useState<ToolWithServer[]>([]);
  const [stats, setStats] = useState<MCPStatsRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [newServerName, setNewServerName] = useState('');
  const [newServerVersion, setNewServerVersion] = useState('1.0.0');
  const [newServerDescription, setNewServerDescription] = useState('');
  const [creatingServer, setCreatingServer] = useState(false);

  const loadData = React.useCallback(async () => {
    setError(null);
    try {
      const serversResponse = await request<{ servers?: MCPServerRecord[] }>('/mcp/servers');
      const serverList = serversResponse.servers || [];
      setServers(serverList);

      const statsResponse = await request<{ stats?: MCPStatsRecord }>('/mcp/stats').catch(() => ({ stats: {} }));
      setStats(statsResponse.stats || null);

      const toolResponses = await Promise.all(
        serverList.map(async (entry) => {
          const payload = await request<{ tools?: MCPToolRecord[] }>(`/mcp/servers/${entry.server_id}/tools`).catch(() => ({ tools: [] }));
          return (payload.tools || []).map((tool) => ({
            ...tool,
            serverName: entry.name,
          }));
        })
      );
      setTools(toolResponses.flat());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load MCP client data');
      setServers([]);
      setTools([]);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function init() {
      setLoading(true);
      await loadData();
      if (!cancelled) {
        setLoading(false);
      }
    }
    void init();
    return () => {
      cancelled = true;
    };
  }, [loadData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  const handleDeleteServer = async (serverId: string) => {
    try {
      await request(`/mcp/servers/${serverId}`, { method: 'DELETE' });
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete server');
    }
  };

  const handleCreateServer = async () => {
    if (!newServerName.trim()) return;
    setCreatingServer(true);
    try {
      await request('/mcp/servers', {
        method: 'POST',
        body: JSON.stringify({
          name: newServerName.trim(),
          version: newServerVersion.trim() || '1.0.0',
          description: newServerDescription.trim(),
        }),
      });
      setIsAddServerOpen(false);
      setNewServerName('');
      setNewServerVersion('1.0.0');
      setNewServerDescription('');
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create server');
    } finally {
      setCreatingServer(false);
    }
  };

  const filteredTools = useMemo(() => {
    const needle = searchQuery.trim().toLowerCase();
    if (!needle) return tools;
    return tools.filter((entry) =>
      `${entry.name} ${entry.description} ${entry.serverName}`.toLowerCase().includes(needle)
    );
  }, [searchQuery, tools]);

  const toolCountByServer = useMemo(() => {
    const counts = new Map<number, number>();
    for (const tool of tools) {
      counts.set(tool.server_id, (counts.get(tool.server_id) || 0) + 1);
    }
    return counts;
  }, [tools]);

  return (
    <div className="space-y-8 animate-in fade-in duration-500" aria-busy={loading || refreshing}>
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">MCP Client Configuration</h2>
          <p className="text-gray-400">Live MCP server connectivity and tool inventory.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => void handleRefresh()} disabled={refreshing} aria-label="Refresh MCP client data">
            <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button onClick={() => setIsAddServerOpen(true)} className="bg-blue-600 hover:bg-blue-700" aria-label="Add new server connection">
            <Plus className="mr-2 h-4 w-4" /> Add New Server Connection
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-red-500/30 bg-red-500/10" role="alert">
          <CardContent className="p-4 text-sm text-red-300">{error}</CardContent>
        </Card>
      )}

      <Card className="border-white/10">
        <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
          <div className="flex justify-between items-center">
            <CardTitle className="text-lg flex items-center gap-2">
              <Server className="h-5 w-5 text-blue-400" /> Connected MCP Servers
            </CardTitle>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Active: {stats?.active_servers ?? servers.filter((entry) => entry.status === 'active').length}
            {' '}| Total: {stats?.total_servers ?? servers.length}
            {' '}| Tools: {stats?.total_tools ?? tools.length}
          </p>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">
          {loading && <div className="text-sm text-gray-400">Loading servers...</div>}
          {!loading && servers.length === 0 && (
            <div className="text-sm text-gray-400">No MCP servers configured yet.</div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {servers.map((server) => (
              <Card key={server.server_id} className="bg-white/5 border-white/10 hover:border-white/30 transition-all">
                <CardContent className="p-4 space-y-3">
                  <div className="flex justify-between items-start">
                    <div className="flex items-center gap-2">
                      <Globe className="h-4 w-4 text-blue-400" />
                      <span className="font-bold text-sm truncate max-w-[140px]" title={server.name}>{server.name}</span>
                    </div>
                    <Badge variant={server.status === 'active' ? 'success' : 'secondary'} className="text-[10px]">
                      {server.status === 'active' ? (
                        <span className="flex items-center gap-1"><CheckCircle className="h-3 w-3" /> Active</span>
                      ) : (
                        server.status
                      )}
                    </Badge>
                  </div>

                  <div className="text-[10px] text-gray-500 font-mono">{server.server_id}</div>
                  <div className="text-xs text-gray-400">v{server.version}</div>

                  <div className="grid grid-cols-2 gap-2 text-center text-[10px] bg-black/20 rounded p-2">
                    <div>
                      <div className="font-bold text-white">{toolCountByServer.get(server.id) || 0}</div>
                      <div className="text-gray-500">Tools</div>
                    </div>
                    <div>
                      <div className="font-bold text-white">{server.status === 'active' ? 'Online' : 'Offline'}</div>
                      <div className="text-gray-500">Health</div>
                    </div>
                  </div>

                  <div className="flex justify-between items-center pt-2 border-t border-white/5">
                    <Button size="icon" variant="ghost" className="h-6 w-6 text-gray-400" aria-label={`Inspect settings for ${server.name}`}>
                      <Settings className="h-3 w-3" />
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-6 w-6 text-red-400 hover:text-red-300 hover:bg-red-900/20"
                      onClick={() => void handleDeleteServer(server.server_id)}
                      aria-label={`Delete server ${server.name}`}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card className="border-white/10">
        <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
          <CardTitle className="text-lg flex items-center gap-2">
            <Search className="h-5 w-5 text-yellow-400" /> MCP Tool Registry
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6 pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" aria-hidden="true" />
            <Input
              placeholder="Search tools by name or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-white/5 border-white/10 pl-9"
              aria-label="Search MCP tools"
            />
          </div>

          {filteredTools.length === 0 && (
            <div className="text-sm text-gray-400">No tools matched your search.</div>
          )}

          <div className="space-y-4">
            {filteredTools.map((tool) => (
              <div key={tool.id} className="flex flex-col md:flex-row items-start md:items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10 gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-sm font-bold text-white">{tool.name}</span>
                    <Badge variant="outline" className="text-[10px]">{tool.serverName}</Badge>
                  </div>
                  <p className="text-sm text-gray-400">{tool.description}</p>
                  <div className="flex gap-4 mt-2 text-[10px] text-gray-500 font-mono">
                    <span>exec: {tool.stats?.execution_count || 0}</span>
                    <span>success: {tool.stats?.success_count || 0}</span>
                    <span>fail: {tool.stats?.failure_count || 0}</span>
                  </div>
                </div>
                <Button variant="outline" size="sm">Inspect</Button>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      <Dialog open={isAddServerOpen} onOpenChange={setIsAddServerOpen}>
        <DialogContent className="bg-gray-900 border border-white/10 text-white max-w-2xl">
          <DialogHeader>
            <DialogTitle>Add New MCP Server Connection</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-500 uppercase">Server Name</label>
              <Input
                id="mcp-server-name"
                value={newServerName}
                onChange={(e) => setNewServerName(e.target.value)}
                placeholder="e.g. Notion MCP"
                className="bg-black/20 border-white/10"
                aria-label="Server name"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-500 uppercase">Version</label>
              <Input
                id="mcp-server-version"
                value={newServerVersion}
                onChange={(e) => setNewServerVersion(e.target.value)}
                placeholder="1.0.0"
                className="bg-black/20 border-white/10"
                aria-label="Server version"
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-500 uppercase">Description</label>
              <Input
                id="mcp-server-description"
                value={newServerDescription}
                onChange={(e) => setNewServerDescription(e.target.value)}
                placeholder="Server purpose and ownership"
                className="bg-black/20 border-white/10"
                aria-label="Server description"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddServerOpen(false)}>Cancel</Button>
            <Button className="bg-blue-600 hover:bg-blue-700" onClick={() => void handleCreateServer()} disabled={creatingServer || !newServerName.trim()}>
              {creatingServer ? 'Adding...' : 'Add Server'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

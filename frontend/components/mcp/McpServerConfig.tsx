'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectItem } from "@/components/ui/select";
import { RefreshCw, Settings, Terminal, Activity, CheckCircle, MessageSquare, Database } from "lucide-react";
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
  input_schema?: unknown;
  stats?: {
    execution_count?: number;
    success_count?: number;
    failure_count?: number;
  };
  last_executed?: string | null;
}

interface MCPResourceRecord {
  id: number;
  name: string;
  description?: string;
  uri: string;
}

interface MCPPromptRecord {
  id: number;
  name: string;
  description?: string;
  arguments?: Array<{ name?: string }>;
}

interface MCPServerDetails {
  tools: MCPToolRecord[];
  resources: MCPResourceRecord[];
  prompts: MCPPromptRecord[];
}

export function McpServerConfig() {
  const [servers, setServers] = useState<MCPServerRecord[]>([]);
  const [selectedServerId, setSelectedServerId] = useState('');
  const [tools, setTools] = useState<MCPToolRecord[]>([]);
  const [resources, setResources] = useState<MCPResourceRecord[]>([]);
  const [prompts, setPrompts] = useState<MCPPromptRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTool, setSelectedTool] = useState<MCPToolRecord | null>(null);

  const selectedServer = useMemo(
    () => servers.find((entry) => entry.server_id === selectedServerId) || null,
    [servers, selectedServerId]
  );

  const fetchServers = React.useCallback(async () => {
    setError(null);
    try {
      const data = await request<{ servers?: MCPServerRecord[] }>('/mcp/servers');
      const nextServers = data.servers || [];
      setServers(nextServers);
      if (!selectedServerId && nextServers.length > 0) {
        setSelectedServerId(nextServers[0].server_id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load MCP servers');
    }
  }, [selectedServerId]);

  const fetchServerDetails = React.useCallback(async (serverId: string): Promise<MCPServerDetails> => {
    if (!serverId) {
      return { tools: [], resources: [], prompts: [] };
    }
    setError(null);
    try {
      const [toolData, resourceData, promptData] = await Promise.all([
        request<{ tools?: MCPToolRecord[] }>(`/mcp/servers/${serverId}/tools`),
        request<{ resources?: MCPResourceRecord[] }>(`/mcp/servers/${serverId}/resources`),
        request<{ prompts?: MCPPromptRecord[] }>(`/mcp/servers/${serverId}/prompts`),
      ]);
      return {
        tools: toolData.tools || [],
        resources: resourceData.resources || [],
        prompts: promptData.prompts || [],
      };
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load MCP server details');
      return { tools: [], resources: [], prompts: [] };
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function init() {
      setLoading(true);
      await fetchServers();
      if (!cancelled) {
        setLoading(false);
      }
    }
    void init();
    return () => {
      cancelled = true;
    };
  }, [fetchServers]);

  useEffect(() => {
    let cancelled = false;
    async function loadDetails() {
      const details = await fetchServerDetails(selectedServerId);
      if (cancelled) return;
      setTools(details.tools);
      setResources(details.resources);
      setPrompts(details.prompts);
    }
    void loadDetails();
    return () => {
      cancelled = true;
    };
  }, [fetchServerDetails, selectedServerId]);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchServers();
    const details = await fetchServerDetails(selectedServerId);
    setTools(details.tools);
    setResources(details.resources);
    setPrompts(details.prompts);
    setRefreshing(false);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white">MCP Server Configuration</h2>
          <p className="text-gray-400">Live server/tool/resource inventory from `/api/v1/mcp/*`.</p>
        </div>
        <Button variant="outline" onClick={() => void handleRefresh()} disabled={refreshing}>
          <RefreshCw className={`mr-2 h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <Card className="border-red-500/30 bg-red-500/10">
          <CardContent className="p-4 text-sm text-red-300">
            {error}
          </CardContent>
        </Card>
      )}

      <Card className="border-white/10">
        <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5 text-blue-400" /> Server Instance
          </CardTitle>
        </CardHeader>
        <CardContent className="pt-6 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-end">
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase text-gray-500">Server</label>
              <Select value={selectedServerId} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setSelectedServerId(e.target.value)} className="bg-white/5 border-white/10 text-white">
                {servers.length === 0 && (
                  <SelectItem value="">No server found</SelectItem>
                )}
                {servers.map((entry) => (
                  <SelectItem key={entry.server_id} value={entry.server_id}>
                    {entry.name} ({entry.server_id})
                  </SelectItem>
                ))}
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <Badge variant={selectedServer?.status === 'active' ? 'success' : 'secondary'} className="text-xs">
                {selectedServer?.status === 'active' ? (
                  <span className="flex items-center gap-1"><CheckCircle className="h-3 w-3" /> Active</span>
                ) : (
                  selectedServer?.status || 'Unknown'
                )}
              </Badge>
              {selectedServer && <span className="text-xs text-gray-400">v{selectedServer.version}</span>}
            </div>
          </div>

          {selectedServer && (
            <div className="text-sm text-gray-300">
              {selectedServer.description || 'No description provided for this MCP server.'}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <Card className="bg-white/5 border-white/10">
              <CardContent className="p-4">
                <div className="text-gray-400 uppercase tracking-wider mb-1">Tools</div>
                <div className="text-xl font-bold text-white">{tools.length}</div>
              </CardContent>
            </Card>
            <Card className="bg-white/5 border-white/10">
              <CardContent className="p-4">
                <div className="text-gray-400 uppercase tracking-wider mb-1">Resources</div>
                <div className="text-xl font-bold text-white">{resources.length}</div>
              </CardContent>
            </Card>
            <Card className="bg-white/5 border-white/10">
              <CardContent className="p-4">
                <div className="text-gray-400 uppercase tracking-wider mb-1">Prompts</div>
                <div className="text-xl font-bold text-white">{prompts.length}</div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      <Card className="border-white/10">
        <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
          <CardTitle className="text-lg flex items-center gap-2">
            <Terminal className="h-5 w-5 text-purple-400" /> Exposed Tools
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 pt-6">
          {loading && <div className="text-sm text-gray-400">Loading tools...</div>}
          {!loading && tools.length === 0 && (
            <div className="text-sm text-gray-400">No tools registered for this server.</div>
          )}
          {tools.map((tool) => (
            <div key={tool.id} className="flex flex-col md:flex-row items-start md:items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10 gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-sm text-blue-400 font-bold">{tool.name}</span>
                  <Badge variant="outline" className="text-[10px] h-5">
                    exec: {tool.stats?.execution_count || 0}
                  </Badge>
                </div>
                <p className="text-sm text-gray-400 mt-1">{tool.description}</p>
                <div className="flex gap-4 mt-2 text-[10px] text-gray-500 font-mono">
                  <span>success: {tool.stats?.success_count || 0}</span>
                  <span>fail: {tool.stats?.failure_count || 0}</span>
                  <span>last: {tool.last_executed || 'never'}</span>
                </div>
              </div>
              <Button size="sm" variant="outline" onClick={() => setSelectedTool(tool)}>Inspect</Button>
            </div>
          ))}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <Card className="border-white/10">
          <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
            <CardTitle className="text-lg flex items-center gap-2">
              <Database className="h-5 w-5 text-yellow-400" /> Exposed Resources
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 pt-6">
            {resources.length === 0 && <div className="text-sm text-gray-400">No resources found.</div>}
            {resources.map((entry) => (
              <div key={entry.id} className="p-3 bg-white/5 rounded-lg border border-white/10">
                <div className="font-mono text-xs font-bold text-yellow-500">{entry.name}</div>
                <p className="text-xs text-gray-400 mt-1">{entry.description || 'No description available.'}</p>
                <code className="block bg-black/30 p-2 rounded text-[10px] text-gray-500 font-mono break-all mt-2">{entry.uri}</code>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-white/10">
          <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
            <CardTitle className="text-lg flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-pink-400" /> Exposed Prompts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 pt-6">
            {prompts.length === 0 && <div className="text-sm text-gray-400">No prompts found.</div>}
            {prompts.map((entry) => (
              <div key={entry.id} className="p-3 bg-white/5 rounded-lg border border-white/10">
                <div className="font-mono text-xs font-bold text-pink-500">{entry.name}</div>
                <p className="text-xs text-gray-400 mt-1">{entry.description || 'No description available.'}</p>
                <div className="flex gap-1 flex-wrap mt-2">
                  {(entry.arguments || []).map((arg, index) => (
                    <span key={`${entry.id}-${index}`} className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded text-gray-300 font-mono">
                      {arg.name || `arg_${index + 1}`}
                    </span>
                  ))}
                  {(entry.arguments || []).length === 0 && (
                    <span className="text-[10px] text-gray-500">No prompt arguments defined.</span>
                  )}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Dialog open={Boolean(selectedTool)} onOpenChange={(open) => !open && setSelectedTool(null)}>
        <DialogContent className="bg-gray-900 border border-white/10 text-white max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5 text-gray-400" /> Tool: <span className="font-mono text-blue-400">{selectedTool?.name}</span>
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="text-sm text-gray-300">{selectedTool?.description}</p>
            <div className="space-y-2">
              <label className="text-xs font-bold text-gray-500 uppercase">Input Schema (JSON)</label>
              <pre className="bg-black/50 p-3 rounded-lg border border-white/10 font-mono text-xs text-gray-300 max-h-[240px] overflow-auto">
{JSON.stringify(selectedTool?.input_schema || {}, null, 2)}
              </pre>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedTool(null)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

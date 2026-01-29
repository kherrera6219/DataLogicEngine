'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectItem } from "@/components/ui/select";
import { 
  Plus, Search, Server, Settings, Trash2, RefreshCw, Download, 
  HardDrive, MessageSquare, Globe,
  CheckCircle, Eye, EyeOff
} from "lucide-react";
import { McpServer, McpTool } from './types';

export function McpClientConfig() {
  const [isAddServerOpen, setIsAddServerOpen] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Mock Data: Connected Servers
  const servers: McpServer[] = [
    { id: '1', name: 'Google Drive MCP', type: 'enterprise', status: 'connected', url: 'wss://mcp.google.com/drive', protocol: 'websocket', toolsCount: 12, resourcesCount: 5, promptsCount: 3, latencyMs: 145, lastActivity: '2 mins ago' },
    { id: '2', name: 'Slack MCP', type: 'enterprise', status: 'connected', url: 'wss://mcp.slack.com/api', protocol: 'websocket', toolsCount: 18, resourcesCount: 8, promptsCount: 4, latencyMs: 89, lastActivity: '12 secs ago' },
    { id: '3', name: 'Salesforce MCP', type: 'enterprise', status: 'connected', url: 'wss://mcp.salesforce.com/api', protocol: 'websocket', toolsCount: 24, resourcesCount: 12, promptsCount: 6, latencyMs: 234, lastActivity: '5 mins ago' },
    { id: '4', name: 'GitHub MCP', type: 'devops', status: 'connected', url: 'wss://mcp.github.com/api', protocol: 'websocket', toolsCount: 32, resourcesCount: 15, promptsCount: 8, latencyMs: 178, lastActivity: '8 mins ago' },
    { id: '5', name: 'PostgreSQL MCP', type: 'devops', status: 'connected', url: 'stdio://localhost/postgres-mcp', protocol: 'stdio', toolsCount: 15, resourcesCount: 20, promptsCount: 5, latencyMs: 12, lastActivity: '1 min ago' },
    { id: '6', name: 'Canva MCP', type: 'data', status: 'connected', url: 'wss://mcp.canva.com/api', protocol: 'websocket', toolsCount: 8, resourcesCount: 4, promptsCount: 2, latencyMs: 312, lastActivity: '45 mins ago' },
    { id: '7', name: 'Web Browser MCP', type: 'data', status: 'connected', url: 'stdio://localhost/puppeteer-mcp', protocol: 'stdio', toolsCount: 22, resourcesCount: 0, promptsCount: 4, latencyMs: 45, lastActivity: '3 mins ago' },
    { id: '8', name: 'Stripe MCP', type: 'other', status: 'disconnected', url: 'wss://mcp.stripe.com/api', protocol: 'websocket', toolsCount: 0, resourcesCount: 0, promptsCount: 0, latencyMs: 0, lastActivity: 'Never', errorMessage: 'Authentication failed (Invalid API key)' },
  ];

  // Mock Data: Tool Registry (Subset)
  const registryTools: McpTool[] = [
    { name: 'query_knowledge', server: 'UKG Production', category: 'Knowledge Operations', description: 'Query the 13-dimensional UKG knowledge graph', isEnabled: true, callsToday: 5234, avgTimeMs: 1200, successRate: 99.8 },
    { name: 'slack_send_message', server: 'Slack MCP', category: 'Communication', description: 'Send a message to a Slack channel or user', isEnabled: true, callsToday: 892, avgTimeMs: 400, successRate: 100 },
    { name: 'github_search_code', server: 'GitHub MCP', category: 'DevOps', description: 'Search code across repositories', isEnabled: true, callsToday: 1234, avgTimeMs: 800, successRate: 98.5 },
  ];

  const filteredTools = registryTools.filter(t => 
    t.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    t.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
       
       <div className="flex justify-between items-center">
          <div>
             <h2 className="text-2xl font-bold text-white">MCP Client Configuration</h2>
             <p className="text-gray-400">Connect UKG to external MCP servers and tool ecosystems</p>
          </div>
          <Button onClick={() => setIsAddServerOpen(true)} className="bg-blue-600 hover:bg-blue-700">
             <Plus className="mr-2 h-4 w-4" /> Add New Server Connection
          </Button>
       </div>

       {/* 📡 Connected MCP Servers */}
       <Card className="border-white/10">
          <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
             <div className="flex justify-between items-center">
                <CardTitle className="text-lg flex items-center gap-2">
                   <Server className="h-5 w-5 text-blue-400" /> Connected MCP Servers
                </CardTitle>
                <div className="flex gap-2">
                   <Button variant="outline" size="sm">
                      <Download className="mr-2 h-4 w-4" /> Import Config
                   </Button>
                </div>
             </div>
             <p className="text-xs text-gray-500 mt-1">Active Connections: {servers.filter(s => s.status === 'connected').length} | Available Tools: 277</p>
          </CardHeader>
          <CardContent className="space-y-6 pt-6">
             <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {servers.map((server) => (
                   <Card key={server.id} className="bg-white/5 border-white/10 hover:border-white/30 transition-all">
                      <CardContent className="p-4 space-y-3">
                         <div className="flex justify-between items-start">
                            <div className="flex items-center gap-2">
                               {server.name.includes('Drive') && <HardDrive className="h-4 w-4 text-green-400" />}
                               {server.name.includes('GitHub') && <Settings className="h-4 w-4 text-gray-400" />}
                               {server.name.includes('Slack') && <MessageSquare className="h-4 w-4 text-purple-400" />}
                               {!server.name.includes('Drive') && !server.name.includes('GitHub') && !server.name.includes('Slack') && <Globe className="h-4 w-4 text-blue-400" />}
                               <span className="font-bold text-sm truncate max-w-[120px]" title={server.name}>{server.name}</span>
                            </div>
                            <Badge variant={server.status === 'connected' ? 'success' : 'destructive'} className="text-[10px]">
                               {server.status === 'connected' ? 'Connected' : 'Disconnected'}
                            </Badge>
                         </div>
                         
                         <div className="font-mono text-[10px] text-gray-500 truncate">{server.url}</div>
                         
                         {server.status === 'connected' ? (
                            <div className="grid grid-cols-3 gap-2 text-center text-[10px] bg-black/20 rounded p-2">
                               <div>
                                  <div className="font-bold text-white">{server.toolsCount}</div>
                                  <div className="text-gray-500">Tools</div>
                               </div>
                               <div>
                                  <div className="font-bold text-white">{server.resourcesCount}</div>
                                  <div className="text-gray-500">Resources</div>
                               </div>
                               <div>
                                  <div className="font-bold text-white">{server.promptsCount}</div>
                                  <div className="text-gray-500">Prompts</div>
                               </div>
                            </div>
                         ) : (
                            <div className="text-[10px] text-red-400 bg-red-900/10 p-2 rounded">
                               {server.errorMessage}
                            </div>
                         )}

                         <div className="flex justify-between items-center pt-2 border-t border-white/5">
                            <span className="text-[10px] text-gray-500 text-ellipsis overflow-hidden whitespace-nowrap max-w-[100px]">Last: {server.lastActivity}</span>
                            <div className="flex gap-1">
                               {server.status === 'disconnected' ? (
                                  <Button size="icon" variant="ghost" className="h-6 w-6 text-yellow-400"><RefreshCw className="h-3 w-3" /></Button>
                               ) : (
                                  <Button size="icon" variant="ghost" className="h-6 w-6 text-gray-400"><Settings className="h-3 w-3" /></Button>
                               )}
                               <Button size="icon" variant="ghost" className="h-6 w-6 text-red-400 hover:text-red-300 hover:bg-red-900/20"><Trash2 className="h-3 w-3" /></Button>
                            </div>
                         </div>
                      </CardContent>
                   </Card>
                ))}
            </div>
          </CardContent>
       </Card>

       {/* 📚 MCP Tool Registry Browser */}
       <Card className="border-white/10">
          <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
             <CardTitle className="text-lg flex items-center gap-2">
                <Search className="h-5 w-5 text-yellow-400" /> MCP Tool Registry
             </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6 pt-6">
             <div className="flex gap-4">
                <div className="relative flex-1">
                   <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
                   <Input 
                      placeholder="Search tools by name or description..." 
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="bg-white/5 border-white/10 pl-9"
                   />
                </div>
                <Select defaultValue="all" className="w-[180px] bg-white/5 border-white/10 text-white">
                   <SelectItem value="all">All Categories</SelectItem>
                   <SelectItem value="knowledge">Knowledge Ops</SelectItem>
                   <SelectItem value="devops">DevOps</SelectItem>
                </Select>
             </div>

             <div className="space-y-4">
                {filteredTools.map((tool) => (
                   <div key={tool.name} className="flex flex-col md:flex-row items-start md:items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10 gap-4">
                      <div className="flex-1">
                         <div className="flex items-center gap-2 mb-1">
                            <span className="font-mono text-sm font-bold text-white">{tool.name}</span>
                            <Badge variant="outline" className="text-[10px]">{tool.server}</Badge>
                            <Badge variant="secondary" className="text-[10px] bg-blue-500/10 text-blue-400">{tool.category}</Badge>
                         </div>
                         <p className="text-sm text-gray-400">{tool.description}</p>
                         <div className="flex gap-4 mt-2 text-[10px] text-gray-500 font-mono">
                            <span>Usage: {tool.callsToday.toLocaleString()}/day</span>
                            <span>Success: {tool.successRate}%</span>
                         </div>
                      </div>
                      <Button variant="outline" size="sm">Configure</Button>
                   </div>
                ))}
             </div>
             <Button variant="ghost" className="w-full text-gray-500 hover:text-white">Load More Tools...</Button>
          </CardContent>
       </Card>

       {/* Add Server Modal */}
       <Dialog open={isAddServerOpen} onOpenChange={setIsAddServerOpen}>
          <DialogContent className="bg-gray-900 border border-white/10 text-white max-w-2xl">
             <DialogHeader>
                <DialogTitle>Add New MCP Server Connection</DialogTitle>
             </DialogHeader>
             
             <div className="space-y-6 py-4">
                <div className="grid grid-cols-2 gap-4">
                   <div className="space-y-2">
                      <label className="text-xs font-bold text-gray-500 uppercase">Server Name</label>
                      <Input placeholder="e.g. Notion MCP" className="bg-black/20 border-white/10" />
                   </div>
                   <div className="space-y-2">
                       <label className="text-xs font-bold text-gray-500 uppercase">Connection Type</label>
                       <Select defaultValue="websocket" className="bg-black/20 border-white/10 text-white">
                          <SelectItem value="websocket">WebSocket (wss://)</SelectItem>
                          <SelectItem value="stdio">STDIO (Local)</SelectItem>
                          <SelectItem value="sse">HTTP SSE</SelectItem>
                       </Select>
                   </div>
                </div>

                <div className="space-y-2">
                   <label className="text-xs font-bold text-gray-500 uppercase">Endpoint URL</label>
                   <Input placeholder="wss://mcp.notion.com/api" className="bg-black/20 border-white/10 font-mono" />
                </div>

                <div className="space-y-2">
                   <label className="text-xs font-bold text-gray-500 uppercase">API Key / Token</label>
                   <div className="relative">
                      <Input type={showKey ? "text" : "password"} placeholder="••••••••••••••••••••••••" className="bg-black/20 border-white/10 font-mono pr-10" />
                      <button 
                         onClick={() => setShowKey(!showKey)}
                         className="absolute right-3 top-2.5 text-gray-400 hover:text-white"
                         type="button"
                      >
                         {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                   </div>
                </div>

                <div className="bg-green-500/10 border border-green-500/20 rounded p-4 text-xs">
                   <div className="flex items-center gap-2 text-green-400 font-bold mb-2">
                      <CheckCircle className="h-4 w-4" /> Connection Successful
                   </div>
                   <div className="text-gray-400">
                      Discovered 14 tools, 6 resources, 3 prompts. Ready to connect.
                   </div>
                </div>
             </div>

             <DialogFooter>
                <Button variant="outline" onClick={() => setIsAddServerOpen(false)}>Cancel</Button>
                <Button className="bg-blue-600 hover:bg-blue-700">Add Server & Connect</Button>
             </DialogFooter>
          </DialogContent>
       </Dialog>

    </div>
  );
}

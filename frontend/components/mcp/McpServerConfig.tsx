'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Copy, RefreshCw, Eye, Settings, Terminal, Activity, CheckCircle, AlertCircle, Play, Database, MessageSquare } from "lucide-react";
import { McpTool } from './types';

export function McpServerConfig() {
  const [selectedTool, setSelectedTool] = useState<McpTool | null>(null);
  const [isToolModalOpen, setIsToolModalOpen] = useState(false);

  // Mock Data
  const tools: McpTool[] = [
    { name: 'query_knowledge', server: 'UKG Production', category: 'Core Knowledge', description: 'Query the 13-dimensional UKG knowledge graph', isEnabled: true, callsToday: 5234, avgTimeMs: 1200, successRate: 99.8, complexity: 'T2 (Moderate)' },
    { name: 'resolve_coordinate', server: 'UKG Production', category: 'Core Knowledge', description: 'Convert natural language to 17-axis coordinate', isEnabled: true, callsToday: 4892, avgTimeMs: 300, successRate: 99.9 },
    { name: 'traverse_graph', server: 'UKG Production', category: 'Core Knowledge', description: 'Navigate knowledge graph relationships', isEnabled: true, callsToday: 2145, avgTimeMs: 800, successRate: 99.5 },
    { name: 'simulate_scenario', server: 'UKG Production', category: 'AI Reasoning', description: 'Run multi-perspective POV engine simulation', isEnabled: true, callsToday: 1567, avgTimeMs: 4200, successRate: 98.2 },
    { name: 'validate_compliance', server: 'UKG Production', category: 'AI Reasoning', description: 'Check regulatory compliance (Axis 10-11)', isEnabled: true, callsToday: 3421, avgTimeMs: 2100, successRate: 99.7 },
  ];

  const resources = [
    { name: 'knowledge_pillars', description: 'Access to all 107 PL1107 knowledge pillars', uri: 'ukg://resources/pillars/{pillar_id}', isEnabled: true },
    { name: 'industry_classifications', description: 'NAICS, PSC, SIC, ISIC codes and mappings', uri: 'ukg://resources/industries/{code_system}/{code}', isEnabled: true },
    { name: 'coordinate_schema', description: '17-axis coordinate system documentation', uri: 'ukg://resources/schema/17axis', isEnabled: true },
  ];

  const prompts = [
    { name: 'healthcare_compliance_query', description: 'Template for HIPAA/GDPR healthcare compliance', variables: ['domain', 'regulation', 'jurisdiction'] },
    { name: 'financial_risk_assessment', description: 'Template for financial sector risk analysis', variables: ['asset_class', 'timeframe', 'risk_level'] },
  ];

  const handleConfigureTool = (tool: McpTool) => {
    setSelectedTool(tool);
    setIsToolModalOpen(true);
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
       
       <div className="flex justify-between items-center">
          <div>
             <h2 className="text-2xl font-bold text-white">MCP Server Configuration</h2>
             <p className="text-gray-400">Expose UKG capabilities to external AI agents & frameworks</p>
          </div>
          <div className="flex gap-2">
             <Button variant="outline"><RefreshCw className="mr-2 h-4 w-4" /> Restart Server</Button>
             <Button><Settings className="mr-2 h-4 w-4" /> Advanced Settings</Button>
          </div>
       </div>

       {/* 📡 Server Instance Configuration */}
       <Card className="border-white/10">
          <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
             <CardTitle className="text-lg flex items-center gap-2">
                <Activity className="h-5 w-5 text-blue-400" /> Server Instance Configuration
             </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6 pt-6">
             <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                   <div className="space-y-2">
                      <label className="text-xs font-bold uppercase text-gray-500">Server Name & ID</label>
                      <div className="flex gap-2">
                         <Input value="UKG Production Server" className="bg-white/5 border-white/10" readOnly />
                         <Input value="ukg-server-prod-001" className="bg-white/5 border-white/10 font-mono text-xs w-48" readOnly />
                      </div>
                   </div>
                   
                   <div className="space-y-2">
                      <label className="text-xs font-bold uppercase text-gray-500">Connection Protocol</label>
                      <Select defaultValue="websocket">
                         <SelectTrigger className="bg-white/5 border-white/10">
                            <SelectValue placeholder="Select Protocol" />
                         </SelectTrigger>
                         <SelectContent>
                            <SelectItem value="websocket">WebSocket (Recommended)</SelectItem>
                            <SelectItem value="stdio">STDIO (Local Process)</SelectItem>
                            <SelectItem value="sse">HTTP SSE</SelectItem>
                         </SelectContent>
                      </Select>
                   </div>

                   <div className="space-y-2">
                      <label className="text-xs font-bold uppercase text-gray-500">Endpoint</label>
                      <div className="flex gap-2">
                         <div className="relative flex-1">
                            <Input value="wss://mcp.ukg.ai:7410" className="bg-white/5 border-white/10 font-mono text-green-400" readOnly />
                         </div>
                         <Button variant="outline" size="icon"><Copy className="h-4 w-4" /></Button>
                         <Button variant="secondary">Test</Button>
                      </div>
                   </div>
                </div>

                <div className="space-y-4">
                   <div className="bg-white/5 rounded-lg p-4 border border-white/10 space-y-3">
                      <div className="flex justify-between items-center pb-2 border-b border-white/10">
                         <span className="text-sm font-bold text-gray-300">Status</span>
                         <Badge variant="success" className="bg-green-500/20 text-green-400 border-green-500/50 flex items-center gap-1">
                            <CheckCircle className="h-3 w-3" /> Running
                         </Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-4 text-xs">
                         <div>
                            <span className="text-gray-500 block">Uptime</span>
                            <span className="font-mono text-white">45d 12h 34m</span>
                         </div>
                         <div>
                            <span className="text-gray-500 block">Latency</span>
                            <span className="font-mono text-white">23ms avg</span>
                         </div>
                         <div>
                            <span className="text-gray-500 block">Peak Load</span>
                            <span className="font-mono text-white">847 req/min</span>
                         </div>
                         <div>
                             <span className="text-gray-500 block">Active Clients</span>
                             <span className="font-mono text-white">8</span>
                         </div>
                      </div>
                   </div>

                   <div className="space-y-2">
                      <label className="text-xs font-bold uppercase text-gray-500">Server API Key</label>
                      <div className="flex gap-2">
                         <Input type="password" value="mcp_server_sk_prod_..." className="bg-white/5 border-white/10 font-mono" readOnly />
                         <Button variant="outline" size="icon"><Copy className="h-4 w-4" /></Button>
                      </div>
                   </div>
                </div>
             </div>
          </CardContent>
       </Card>

       {/* 🛠️ Exposed Tools & Capabilities */}
       <Card className="border-white/10">
          <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
             <CardTitle className="text-lg flex items-center gap-2">
                <Terminal className="h-5 w-5 text-purple-400" /> Exposed Tools & Capabilities
             </CardTitle>
          </CardHeader>
          <CardContent className="space-y-8 pt-6">
             
             {/* Tools List */}
             <div>
                <h3 className="text-sm font-bold text-gray-400 mb-4 uppercase tracking-wider">Core Knowledge Operations</h3>
                <div className="space-y-3">
                   {tools.filter(t => t.category === 'Core Knowledge').map((tool) => (
                      <div key={tool.name} className="flex flex-col md:flex-row items-start md:items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10 gap-4">
                         <div className="flex-1">
                            <div className="flex items-center gap-2">
                               <span className="font-mono text-sm text-blue-400 font-bold">{tool.name}</span>
                               <Badge variant={tool.isEnabled ? "success" : "secondary"} className="text-[10px] h-5">
                                  {tool.isEnabled ? 'Active' : 'Disabled'}
                               </Badge>
                            </div>
                            <p className="text-sm text-gray-400 mt-1">{tool.description}</p>
                            <div className="flex gap-4 mt-2 text-[10px] text-gray-500 font-mono">
                               <span>Calls/day: {tool.callsToday.toLocaleString()}</span>
                               <span>Avg time: {tool.avgTimeMs}ms</span>
                               <span className="text-green-500">Success: {tool.successRate}%</span>
                            </div>
                         </div>
                         <div className="flex gap-2">
                            <Button size="sm" variant="outline" onClick={() => handleConfigureTool(tool)}>Configure</Button>
                            <Button size="sm" variant="ghost" className="text-gray-400"><Activity className="h-4 w-4" /></Button>
                         </div>
                      </div>
                   ))}
                </div>
             </div>

             <div>
                <h3 className="text-sm font-bold text-gray-400 mb-4 uppercase tracking-wider">AI Reasoning & Simulation</h3>
                <div className="space-y-3">
                   {tools.filter(t => t.category === 'AI Reasoning').map((tool) => (
                      <div key={tool.name} className="flex flex-col md:flex-row items-start md:items-center justify-between p-4 bg-white/5 rounded-lg border border-white/10 gap-4">
                         <div className="flex-1">
                            <div className="flex items-center gap-2">
                               <span className="font-mono text-sm text-purple-400 font-bold">{tool.name}</span>
                               <Badge variant={tool.isEnabled ? "success" : "secondary"} className="text-[10px] h-5">
                                  {tool.isEnabled ? 'Active' : 'Disabled'}
                               </Badge>
                            </div>
                            <p className="text-sm text-gray-400 mt-1">{tool.description}</p>
                            <div className="flex gap-4 mt-2 text-[10px] text-gray-500 font-mono">
                               <span>Calls/day: {tool.callsToday.toLocaleString()}</span>
                               <span>Avg time: {tool.avgTimeMs}ms</span>
                               <span className="text-green-500">Success: {tool.successRate}%</span>
                            </div>
                         </div>
                         <div className="flex gap-2">
                            <Button size="sm" variant="outline" onClick={() => handleConfigureTool(tool)}>Configure</Button>
                            <Button size="sm" variant="ghost" className="text-gray-400"><Activity className="h-4 w-4" /></Button>
                         </div>
                      </div>
                   ))}
                </div>
             </div>

          </CardContent>
       </Card>

       <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* 📚 Exposed Resources */}
          <Card className="border-white/10">
             <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
                <CardTitle className="text-lg flex items-center gap-2">
                   <Database className="h-5 w-5 text-yellow-400" /> Exposed Resources
                </CardTitle>
             </CardHeader>
             <CardContent className="space-y-4 pt-6">
                {resources.map((res) => (
                   <div key={res.name} className="p-3 bg-white/5 rounded-lg border border-white/10">
                      <div className="flex justify-between items-start mb-1">
                         <span className="font-mono text-xs font-bold text-yellow-500">{res.name}</span>
                         <Badge variant="outline" className="text-[10px] bg-green-500/10 text-green-400 border-green-500/20">Active</Badge>
                      </div>
                      <p className="text-xs text-gray-400 mb-2">{res.description}</p>
                      <code className="block bg-black/30 p-2 rounded text-[10px] text-gray-500 font-mono break-all">{res.uri}</code>
                   </div>
                ))}
             </CardContent>
          </Card>
          
          {/* 💬 Exposed Prompts */}
          <Card className="border-white/10">
             <CardHeader className="bg-white/5 border-b border-white/10 pb-4">
                <CardTitle className="text-lg flex items-center gap-2">
                   <MessageSquare className="h-5 w-5 text-pink-400" /> Exposed Prompts
                </CardTitle>
             </CardHeader>
             <CardContent className="space-y-4 pt-6">
                {prompts.map((prompt) => (
                   <div key={prompt.name} className="p-3 bg-white/5 rounded-lg border border-white/10">
                      <div className="flex justify-between items-start mb-1">
                         <span className="font-mono text-xs font-bold text-pink-500">{prompt.name}</span>
                         <Badge variant="outline" className="text-[10px]">Template</Badge>
                      </div>
                      <p className="text-xs text-gray-400 mb-2">{prompt.description}</p>
                      <div className="flex gap-1 flex-wrap">
                         {prompt.variables.map(v => (
                            <span key={v} className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded text-gray-300 font-mono">{"{"}{v}{"}"}</span>
                         ))}
                      </div>
                   </div>
                ))}
                <Button variant="outline" className="w-full border-dashed border-white/20 text-gray-400 hover:border-white/40 hover:text-white">
                   + Add Custom Prompt Template
                </Button>
             </CardContent>
          </Card>
       </div>

       {/* Tool Configuration Modal */}
       <Dialog open={isToolModalOpen} onOpenChange={setIsToolModalOpen}>
          <DialogContent className="bg-gray-900 border border-white/10 text-white max-w-2xl">
             <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                   <Settings className="h-5 w-5 text-gray-400" /> Tool Configuration: <span className="font-mono text-blue-400">{selectedTool?.name}</span>
                </DialogTitle>
             </DialogHeader>
             
             {selectedTool && (
                <div className="space-y-6 py-4">
                   <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                         <label className="text-xs font-bold text-gray-500 uppercase">Version</label>
                         <div className="text-gray-300">2.1.0</div>
                      </div>
                      <div>
                         <label className="text-xs font-bold text-gray-500 uppercase">Complexity Tier</label>
                         <div className="text-gray-300">{selectedTool.complexity || 'T1 (Basic)'}</div>
                      </div>
                   </div>

                   <div className="space-y-2">
                      <label className="text-xs font-bold text-gray-500 uppercase">Input Schema (JSON)</label>
                      <div className="bg-black/50 p-3 rounded-lg border border-white/10 font-mono text-xs text-gray-300 h-32 overflow-y-auto">
{`{
  "query": "string (required)",
  "axis_hints": {
    "axis_1_pillar": "PL####",
    "axis_2_industry": "NAICS-######"
  },
  "max_results": "integer (default: 10)",
  "confidence_threshold": "float (default: 0.95)"
}`}
                      </div>
                   </div>

                   <div className="space-y-4 pt-4 border-t border-white/10">
                      <h4 className="font-bold text-sm">Performance Settings</h4>
                      
                      <div className="grid grid-cols-2 gap-4">
                         <div className="space-y-2">
                            <label className="text-xs font-bold text-gray-500">Timeout</label>
                            <Select defaultValue="30">
                               <SelectTrigger className="bg-white/5 border-white/10"><SelectValue /></SelectTrigger>
                               <SelectContent><SelectItem value="30">30 seconds</SelectItem></SelectContent>
                            </Select>
                         </div>
                         <div className="space-y-2">
                            <label className="text-xs font-bold text-gray-500">Rate Limit</label>
                            <Select defaultValue="100">
                               <SelectTrigger className="bg-white/5 border-white/10"><SelectValue /></SelectTrigger>
                               <SelectContent><SelectItem value="100">100 calls/min</SelectItem></SelectContent>
                            </Select>
                         </div>
                      </div>
                   </div>
                </div>
             )}

             <DialogFooter>
                <Button variant="outline" onClick={() => setIsToolModalOpen(false)}>Cancel</Button>
                <Button className="bg-blue-600 hover:bg-blue-700">Save Changes</Button>
             </DialogFooter>
          </DialogContent>
       </Dialog>

    </div>
  );
}

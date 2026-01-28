'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Copy, Terminal, Code2, BookOpen, MessageSquare } from "lucide-react";

export function McpIntegrationExamples() {
  const [copied, setCopied] = useState('');

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(''), 2000);
  };

  const pythonExample = `from mcp import MCPClient

# Connect to UKG MCP Server
client = MCPClient(
    uri="wss://mcp.ukg.ai:7410",
    auth_token="mcp_server_sk_prod_a1b2c3d4..."
)

# Initialize connection
await client.initialize()

# Discover available tools
tools = await client.list_tools()
print(f"Available tools: {len(tools)}")

# Call a tool
result = await client.call_tool(
    name="query_knowledge",
    arguments={
        "query": "GDPR compliance for AI",
        "axis_hints": {
            "axis_1_pillar": "PL0012",
            "axis_2_industry": "NAICS-621111"
        },
        "confidence_threshold": 0.995
    }
)

# Process results
for item in result['results']:
    print(f"Coordinate: {item['coordinate']}")
    print(f"Confidence: {item['confidence']}")
    print(f"Content: {item['content']}")`;

  const tsExample = `import { Server } from "@modelcontextprotocol/sdk"

// Create MCP server instance
const server = new Server(
  {
    name: "ukg-mcp-server",
    version: "2.1.0"
  },
  {
    capabilities: {
      tools: {},
      resources: {},
      prompts: {}
    }
  }
);

// Register tool handlers
server.setRequestHandler(
  ListToolsRequestSchema,
  async () => ({
    tools: [
      {
        name: "query_knowledge",
        description: "Query UKG graph",
        inputSchema: {
          type: "object",
          properties: {
            query: { type: "string" },
            axis_hints: { type: "object" }
          },
          required: ["query"]
        }
      }
    ]
  })
);

// Start server on WebSocket
const transport = new WebSocketServerTransport({
  port: 7410
});

await server.connect(transport);`;

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
       
       <div className="flex justify-between items-center">
          <div>
             <h2 className="text-2xl font-bold text-white">MCP Integration Examples</h2>
             <p className="text-gray-400">Code snippets to connect and extend UKG capabilities</p>
          </div>
          <div className="flex gap-2">
             <Button variant="outline"><BookOpen className="mr-2 h-4 w-4" /> View Full Documentation</Button>
             <Button variant="outline"><MessageSquare className="mr-2 h-4 w-4" /> Get Support</Button>
          </div>
       </div>

       <Tabs defaultValue="python" className="w-full">
          <div className="flex items-center justify-between mb-4">
             <TabsList className="bg-white/5 border border-white/10">
                <TabsTrigger value="python">Python Client</TabsTrigger>
                <TabsTrigger value="ts">TypeScript Server</TabsTrigger>
                <TabsTrigger value="langchain">LangChain</TabsTrigger>
             </TabsList>
          </div>

          <TabsContent value="python" className="mt-0">
             <Card className="border-white/10">
                <CardHeader className="bg-white/5 border-b border-white/10 pb-4 flex flex-row items-center justify-between">
                   <CardTitle className="text-lg flex items-center gap-2">
                      <Terminal className="h-5 w-5 text-blue-400" /> Python Client Example
                   </CardTitle>
                   <Button size="sm" variant="outline" onClick={() => handleCopy(pythonExample, 'python')}>
                      {copied === 'python' ? 'Copied!' : <><Copy className="mr-2 h-3 w-3" /> Copy Code</>}
                   </Button>
                </CardHeader>
                <CardContent className="p-0 bg-black/40">
                   <pre className="p-6 overflow-x-auto text-sm font-mono text-gray-300 leading-relaxed">
                      {pythonExample}
                   </pre>
                </CardContent>
             </Card>
          </TabsContent>

          <TabsContent value="ts" className="mt-0">
             <Card className="border-white/10">
                <CardHeader className="bg-white/5 border-b border-white/10 pb-4 flex flex-row items-center justify-between">
                   <CardTitle className="text-lg flex items-center gap-2">
                      <Code2 className="h-5 w-5 text-yellow-400" /> TypeScript Server Example
                   </CardTitle>
                   <Button size="sm" variant="outline" onClick={() => handleCopy(tsExample, 'ts')}>
                      {copied === 'ts' ? 'Copied!' : <><Copy className="mr-2 h-3 w-3" /> Copy Code</>}
                   </Button>
                </CardHeader>
                <CardContent className="p-0 bg-black/40">
                   <pre className="p-6 overflow-x-auto text-sm font-mono text-gray-300 leading-relaxed">
                      {tsExample}
                   </pre>
                </CardContent>
             </Card>
          </TabsContent>

          <TabsContent value="langchain" className="mt-0">
             <Card className="border-white/10">
                <CardContent className="p-12 text-center text-gray-500">
                   Integration example coming soon...
                </CardContent>
             </Card>
          </TabsContent>

       </Tabs>

    </div>
  );
}

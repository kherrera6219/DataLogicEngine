'use client';

import React from 'react';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Server, Settings, Zap } from "lucide-react";
import { useRouter } from 'next/navigation';

export function McpHub() {
  const router = useRouter();

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      
      {/* 🔌 Header */}
      <section className="grid grid-cols-1 gap-4">
        <Card className="glass-card border-white/10 bg-gradient-to-r from-gray-900 to-black p-6">
          <div className="flex flex-col md:flex-row justify-between items-center text-center md:text-left">
            <div>
              <h1 className="text-2xl font-bold text-white flex items-center gap-3 justify-center md:justify-start">
                <Zap className="h-6 w-6 text-yellow-400" />
                UKG Model Context Protocol (MCP) Hub
              </h1>
              <p className="text-muted-foreground mt-1">
                The Universal AI Connector - Connect Any AI to Any Tool
              </p>
            </div>
            <div className="mt-4 md:mt-0">
               <Badge variant="outline" className="bg-white/5 border-white/10 text-gray-400">v2.1.0 Core</Badge>
            </div>
          </div>
        </Card>
      </section>

      {/* 📊 Ecosystem Overview */}
      <section>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
           {[
              { label: 'Active Servers', value: '24', color: 'text-white' },
              { label: 'Active Clients', value: '8', color: 'text-white' },
              { label: 'Total Tools', value: '277', color: 'text-white' },
              { label: 'Messages Today', value: '12,450', color: 'text-green-400' },
           ].map((stat, i) => (
              <Card key={i} className="bg-white/5 border-white/10 text-center py-4">
                 <div className="text-xs text-gray-400 uppercase tracking-widest mb-1">{stat.label}</div>
                 <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
              </Card>
           ))}
        </div>
      </section>

      {/* 🎯 Quick Actions */}
      <section>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
           <Card className="hover:bg-white/5 transition-colors border-white/10 cursor-pointer group" onClick={() => router.push('/mcp?tab=server')}>
              <CardContent className="pt-6 flex flex-col items-center text-center space-y-4">
                 <div className="p-4 rounded-full bg-blue-500/10 group-hover:bg-blue-500/20 transition-colors">
                    <Server className="h-8 w-8 text-blue-400" />
                 </div>
                 <div>
                    <h3 className="text-lg font-bold text-white">Configure MCP Servers</h3>
                    <p className="text-sm text-gray-400 mt-2">Expose UKG capabilities to external AI agents & frameworks.</p>
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
                    <p className="text-sm text-gray-400 mt-2">Connect UKG to external tools like Slack, GitHub, & Drive.</p>
                 </div>
                 <Button variant="outline" className="w-full border-white/10 hover:bg-white/10" onClick={(e) => { e.stopPropagation(); router.push('/mcp?tab=client'); }}>
                    Connect Clients <ExternalLink className="ml-2 h-4 w-4" />
                 </Button>
              </CardContent>
           </Card>

           <Card className="hover:bg-white/5 transition-colors border-white/10 cursor-pointer group" onClick={() => router.push('/mcp?tab=client')}>
              <CardContent className="pt-6 flex flex-col items-center text-center space-y-4">
                 <div className="p-4 rounded-full bg-green-500/10 group-hover:bg-green-500/20 transition-colors">
                    <Settings className="h-8 w-8 text-green-400" />
                 </div>
                 <div>
                    <h3 className="text-lg font-bold text-white">Browse Tool Registry</h3>
                    <p className="text-sm text-gray-400 mt-2">Explore & configure 277+ ready-to-use tools.</p>
                 </div>
                 <Button variant="outline" className="w-full border-white/10 hover:bg-white/10" onClick={(e) => { e.stopPropagation(); router.push('/mcp?tab=client'); }}>
                    Explore Tools <ExternalLink className="ml-2 h-4 w-4" />
                 </Button>
              </CardContent>
           </Card>
        </div>
      </section>

    </div>
  );
}

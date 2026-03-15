'use client';

import { Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import dynamic from 'next/dynamic';

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ChevronLeft, Server } from 'lucide-react';
import Link from 'next/link';

const McpHub = dynamic(
  () => import('@/components/mcp/McpHub').then((module) => ({ default: module.McpHub })),
  { loading: () => <div className="p-6 text-muted-foreground">Loading hub...</div> }
);
const McpServerConfig = dynamic(
  () => import('@/components/mcp/McpServerConfig').then((module) => ({ default: module.McpServerConfig })),
  { loading: () => <div className="p-6 text-muted-foreground">Loading server config...</div> }
);
const McpClientConfig = dynamic(
  () => import('@/components/mcp/McpClientConfig').then((module) => ({ default: module.McpClientConfig })),
  { loading: () => <div className="p-6 text-muted-foreground">Loading client tools...</div> }
);
const McpAnalytics = dynamic(
  () => import('@/components/mcp/McpAnalytics').then((module) => ({ default: module.McpAnalytics })),
  { loading: () => <div className="p-6 text-muted-foreground">Loading analytics...</div> }
);
const McpIntegrationExamples = dynamic(
  () => import('@/components/mcp/McpIntegrationExamples').then((module) => ({ default: module.McpIntegrationExamples })),
  { loading: () => <div className="p-6 text-muted-foreground">Loading integration examples...</div> }
);

function McpPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const activeTab = searchParams.get('tab') || 'hub';

  return (
    <div className="min-h-full bg-background text-foreground font-sans">
      <div className="min-h-full bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed">

        {/* Acrylic Header */}
        <div className="h-16 border-b border-white/5 fluent-acrylic sticky top-0 z-10 flex items-center gap-4 px-8 backdrop-blur-3xl">
          <Link href="/dashboard">
            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-slate-200/70 dark:hover:bg-white/10 text-slate-600 dark:text-gray-400 shrink-0">
              <ChevronLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex items-center gap-3">
            <div className="bg-emerald-500/10 p-2 rounded-lg border border-emerald-500/20">
              <Server className="h-5 w-5 text-emerald-400" />
            </div>
            <div>
              <h1 className="text-title font-bold text-slate-900 dark:text-gray-100">MCP Hub</h1>
              <div className="text-[10px] text-slate-500 dark:text-gray-500 font-mono uppercase tracking-widest">Model Context Protocol</div>
            </div>
          </div>
        </div>

        <div className="max-w-[1600px] w-full mx-auto p-8 animate-connected-enter">
          <Tabs value={activeTab} onValueChange={(value) => router.push(`/mcp?tab=${value}`)}>
            <TabsList className="bg-white/70 dark:bg-white/5 border border-slate-200 dark:border-white/10 mb-6">
              <TabsTrigger value="hub">Hub Overview</TabsTrigger>
              <TabsTrigger value="server">Server Config</TabsTrigger>
              <TabsTrigger value="client">Client &amp; Tools</TabsTrigger>
              <TabsTrigger value="analytics">Analytics</TabsTrigger>
              <TabsTrigger value="integration">Integration</TabsTrigger>
            </TabsList>

            <TabsContent value="hub" className="mt-0">
              <McpHub />
            </TabsContent>

            <TabsContent value="server" className="mt-0">
              <McpServerConfig />
            </TabsContent>

            <TabsContent value="client" className="mt-0">
              <McpClientConfig />
            </TabsContent>

            <TabsContent value="analytics" className="mt-0">
              <McpAnalytics />
            </TabsContent>

            <TabsContent value="integration" className="mt-0">
              <McpIntegrationExamples />
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}

export default function McpPage() {
   return (
      <Suspense fallback={<div className="p-6 text-foreground">Loading MCP Hub...</div>}>
         <McpPageContent />
      </Suspense>
   );
}

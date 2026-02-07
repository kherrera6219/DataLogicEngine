'use client';

import { Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import dynamic from 'next/dynamic';

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from 'lucide-react';
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
    <div className="flex flex-col h-full rounded-xl border border-slate-200/70 dark:border-white/10 bg-white/70 dark:bg-black/40 text-gray-900 dark:text-white p-6 space-y-6 overflow-y-auto">
       <div className="flex items-center gap-4">
          <Link href="/dashboard">
             <Button variant="ghost" size="icon" className="hover:bg-slate-200/70 dark:hover:bg-white/10 text-slate-600 dark:text-gray-400">
                <ChevronLeft className="h-4 w-4" />
             </Button>
          </Link>
          <Tabs value={activeTab} onValueChange={(value) => router.push(`/mcp?tab=${value}`)} className="w-full">
             <div className="flex items-center justify-between mb-6">
                <TabsList className="bg-white/70 dark:bg-white/5 border border-slate-200 dark:border-white/10">
                   <TabsTrigger value="hub">Hub Overview</TabsTrigger>
                   <TabsTrigger value="server">Server Config</TabsTrigger>
                   <TabsTrigger value="client">Client & Tools</TabsTrigger>
                   <TabsTrigger value="analytics">Analytics</TabsTrigger>
                   <TabsTrigger value="integration">Integration</TabsTrigger>
                </TabsList>
             </div>

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
  );
}

export default function McpPage() {
   return (
      <Suspense fallback={<div className="p-6 text-foreground">Loading MCP Hub...</div>}>
         <McpPageContent />
      </Suspense>
   );
}

'use client';

import { Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { McpHub } from '@/components/mcp/McpHub';
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ChevronLeft } from 'lucide-react';
import Link from 'next/link';
import { McpServerConfig } from '@/components/mcp/McpServerConfig';
import { McpClientConfig } from '@/components/mcp/McpClientConfig';
import { McpAnalytics } from '@/components/mcp/McpAnalytics';
import { McpIntegrationExamples } from '@/components/mcp/McpIntegrationExamples';

function McpPageContent() {
  const searchParams = useSearchParams();
  const activeTab = searchParams.get('tab') || 'hub';

  return (
    <div className="flex flex-col h-full bg-black/40 text-white p-6 space-y-6 overflow-y-auto">
       <div className="flex items-center gap-4">
          <Link href="/dashboard">
             <Button variant="ghost" size="icon" className="hover:bg-white/10 text-gray-400">
                <ChevronLeft className="h-4 w-4" />
             </Button>
          </Link>
          <Tabs value={activeTab} onValueChange={() => {}} className="w-full">
             <div className="flex items-center justify-between mb-6">
                <TabsList className="bg-white/5 border border-white/10">
                   <Link href="/mcp?tab=hub"><TabsTrigger value="hub">Hub Overview</TabsTrigger></Link>
                   <Link href="/mcp?tab=server"><TabsTrigger value="server">Server Config</TabsTrigger></Link>
                   <Link href="/mcp?tab=client"><TabsTrigger value="client">Client & Tools</TabsTrigger></Link>
                   <Link href="/mcp?tab=analytics"><TabsTrigger value="analytics">Analytics</TabsTrigger></Link>
                   <Link href="/mcp?tab=integration"><TabsTrigger value="integration">Integration</TabsTrigger></Link>
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
      <Suspense fallback={<div className="p-6 text-white">Loading MCP Hub...</div>}>
         <McpPageContent />
      </Suspense>
   );
}

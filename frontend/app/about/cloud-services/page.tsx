
import { Cloud, Server, Database, Lock, WifiOff } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function CloudServicesPage() {
  return (
    <div className="container max-w-4xl py-12 space-y-12">
      <div className="space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">Cloud Architecture & Services</h1>
        <p className="text-xl text-muted-foreground">
          How DataLogicEngine leverages cloud technologies to deliver enterprise-grade knowledge synthesis.
        </p>
      </div>

      <div className="grid gap-8 md:grid-cols-2">
         {/* Architecture Overview */}
         <div className="col-span-2 p-8 rounded-2xl border bg-card text-card-foreground shadow-sm space-y-4">
            <div className="flex items-center gap-3">
               <div className="p-2 w-fit rounded-lg bg-blue-500/10 text-blue-500">
                  <Cloud className="h-6 w-6" />
               </div>
               <h2 className="text-2xl font-bold">Cloud-Only Architecture</h2>
            </div>
            <p className="text-muted-foreground leading-relaxed">
               DataLogicEngine operates as a strictly cloud-dependent application. Unlike traditional desktop software 
               that runs entirely on your machine, this application acts as a secure orchestrator for powerful 
               cloud-based AI models. This architecture allows us to provide reasoning capabilities far beyond 
               what any single local device could compute.
            </p>
            <div className="flex items-center gap-2 text-sm text-amber-500 font-medium bg-amber-500/5 p-3 rounded-lg border border-amber-500/20 w-fit">
               <WifiOff className="h-4 w-4" />
               <span>Continuous internet connection required for all features.</span>
            </div>
         </div>

         {/* AI Providers */}
         <div className="p-6 rounded-xl border bg-card text-card-foreground shadow-sm space-y-4">
            <div className="flex items-center gap-3">
               <div className="p-2 w-fit rounded-lg bg-purple-500/10 text-purple-500">
                  <Server className="h-6 w-6" />
               </div>
               <h3 className="text-xl font-semibold">AI Providers</h3>
            </div>
            <p className="text-sm text-muted-foreground">
               We utilize a specialized &quot;Circuit Breaker&quot; system to route queries to the best available model. 
               Your data may be processed by one of the following trusted enterprise partners:
            </p>
            <ul className="space-y-2 text-sm">
               <li className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-green-500" /> OpenAI (GPT-4o)
               </li>
               <li className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-blue-500" /> Microsoft Azure OpenAI
               </li>
               <li className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-orange-500" /> Anthropic (Claude 3.5)
               </li>
               <li className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-red-500" /> Google Vertex AI
               </li>
            </ul>
         </div>

         {/* Data Handling */}
         <div className="p-6 rounded-xl border bg-card text-card-foreground shadow-sm space-y-4">
            <div className="flex items-center gap-3">
               <div className="p-2 w-fit rounded-lg bg-green-500/10 text-green-500">
                  <Database className="h-6 w-6" />
               </div>
               <h3 className="text-xl font-semibold">Data Privacy</h3>
            </div>
            <p className="text-sm text-muted-foreground">
               We adhere to strict &quot;Zero Retention&quot; policies for standard inference where possible.
            </p>
             <ul className="space-y-3 text-sm">
               <li className="flex gap-2">
                  <Lock className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
                  <span>Queries are encrypted in transit (TLS 1.3) and at rest (AES-256).</span>
               </li>
               <li className="flex gap-2">
                  <Lock className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
                  <span>We do not use your data to train public AI models.</span>
               </li>
               <li className="flex gap-2">
                  <Lock className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
                  <span>Enterprise agreements with providers ensure rigorous data silos.</span>
               </li>
            </ul>
         </div>
      </div>
      
      <div className="flex justify-center pt-8">
         <Button asChild variant="outline">
            <Link href="/about/privacy">View Full Privacy Policy</Link>
         </Button>
      </div>
    </div>
  );
}

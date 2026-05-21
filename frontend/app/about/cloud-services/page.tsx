'use client';

import React from 'react';
import { Cloud, Database, Lock, Globe, Server, UserCheck } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

export default function CloudServicesPage() {
  const providers = [
    {
      name: "OpenAI",
      usage: "Optional provider for configured AI reasoning requests.",
      data: "Prompt text and any context you include in the request.",
      residency: "Handled under the provider account and region settings you configure."
    },
    {
      name: "Anthropic",
      usage: "Optional provider for configured long-context AI requests.",
      data: "Prompt text and any context you include in the request.",
      residency: "Handled under the provider account and region settings you configure."
    },
    {
      name: "Google Gemini / Vertex AI",
      usage: "Optional provider for configured AI reasoning requests.",
      data: "Prompt text and any context you include in the request.",
      residency: "Handled under the provider account and region settings you configure."
    },
    {
      name: "Microsoft Azure OpenAI",
      usage: "Optional OpenAI-compatible deployment for configured enterprise environments.",
      data: "Prompt text and any context you include in the request.",
      residency: "Handled under the Azure resource and region settings you configure."
    }
  ];

  return (
    <div className="container mx-auto py-12 px-4 max-w-5xl space-y-12">
      <header className="space-y-4 text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-500 text-xs font-bold tracking-widest uppercase">
          <Globe className="h-3 w-3" /> Data Sovereignty
        </div>
        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tighter">Cloud Services & Residency</h1>
        <p className="text-xl text-muted-foreground max-w-3xl mx-auto font-medium">
          DataLogicEngine is built on a &quot;Local-First, Cloud-Augmented&quot; philosophy. Here is how we manage your information.
        </p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="border-premium bg-background/50">
          <CardHeader>
            <Database className="h-8 w-8 text-blue-500 mb-2" />
            <CardTitle>Local Storage</CardTitle>
            <CardDescription>Your data stays with you.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            In the Windows desktop build, user profiles, chat history, provider settings, and local app data are stored on the workstation. Cloud database connections are optional configuration paths for future or managed deployments.
          </CardContent>
        </Card>

        <Card className="border-premium bg-background/50">
          <CardHeader>
            <Cloud className="h-8 w-8 text-violet-500 mb-2" />
            <CardTitle>Cloud AI Requests</CardTitle>
            <CardDescription>Internet required for AI reasoning.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            AI reasoning uses configured third-party providers. Prompts and selected context may be sent over the internet to the provider you configure, and responses should be verified before critical use.
          </CardContent>
        </Card>

        <Card className="border-premium bg-background/50">
          <CardHeader>
            <Lock className="h-8 w-8 text-emerald-500 mb-2" />
            <CardTitle>Provider Policies</CardTitle>
            <CardDescription>Controlled by provider configuration.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Data retention, logging, training, and regional handling depend on the third-party provider account, contract, and API settings you use. Review those provider terms before sending sensitive content.
          </CardContent>
        </Card>
      </div>

      <section className="space-y-6">
        <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
          <Server className="text-blue-500 h-8 w-8" /> 
          Verified Cloud Providers
        </h2>
        <div className="grid grid-cols-1 gap-4">
          {providers.map(p => (
            <div key={p.name} className="p-6 rounded-2xl bg-muted/30 border border-white/5 hover:border-white/10 transition-all flex flex-col md:flex-row justify-between gap-6">
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-foreground">{p.name}</h3>
                <p className="text-sm text-muted-foreground">{p.usage}</p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 min-w-[300px]">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground block mb-1">Data Shared</span>
                  <span className="text-sm font-medium">{p.data}</span>
                </div>
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground block mb-1">Processing Region</span>
                  <span className="text-sm font-medium">{p.residency}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="p-10 rounded-[2.5rem] bg-gradient-to-br from-blue-600/10 to-violet-600/10 border border-blue-500/20 space-y-6 relative overflow-hidden">
        <div className="relative z-10 space-y-4">
          <div className="flex items-center gap-3 text-blue-500">
            <UserCheck className="h-8 w-8" />
            <h2 className="text-2xl font-bold">Your Privacy Controls</h2>
          </div>
          <p className="text-lg leading-relaxed text-muted-foreground">
            In <strong>Settings &gt; Privacy</strong>, you can export local data, request local profile deletion, and manage chat history behavior. In AI model settings, you can disable AI processing or choose which configured provider is used.
          </p>
        </div>
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 blur-[100px] pointer-events-none" />
      </section>

      <footer className="text-center text-muted-foreground text-sm py-8">
        <p>&copy; 2026 DataLogicEngine. Cloud and AI behavior depends on the providers and deployment mode you configure.</p>
      </footer>
    </div>
  );
}

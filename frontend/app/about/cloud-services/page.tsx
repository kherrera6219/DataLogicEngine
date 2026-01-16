'use client';

import React from 'react';
import { Cloud, Database, Lock, Globe, Server, UserCheck } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

export default function CloudServicesPage() {
  const providers = [
    {
      name: "OpenAI",
      usage: "Primary reasoning vector for analytical and mathematical tasks.",
      data: "Prompt content only. No metadata or personal identifiers.",
      residency: "Global (Primarily US)"
    },
    {
      name: "Anthropic",
      usage: "Used for long-form reasoning and ethical deconfliction.",
      data: "Prompt content only. Strictly transient processing.",
      residency: "Global (Primarily US)"
    },
    {
      name: "Google Cloud (Vertex AI)",
      usage: "Enterprise search and knowledge graph grounding.",
      data: "Internal vector representations.",
      residency: "Configurable / Regional"
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
            All user profiles, chat history, and configuration files are stored locally in your installation path. We do not maintain a cloud database of your personal files.
          </CardContent>
        </Card>

        <Card className="border-premium bg-background/50">
          <CardHeader>
            <Cloud className="h-8 w-8 text-violet-500 mb-2" />
            <CardTitle>Cloud Intelligence</CardTitle>
            <CardDescription>Intelligence as a Service.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            Reasoning logic is processed in the cloud to provide world-class accuracy. This requires sending your specific query to our verified AI partners.
          </CardContent>
        </Card>

        <Card className="border-premium bg-background/50">
          <CardHeader>
            <Lock className="h-8 w-8 text-emerald-500 mb-2" />
            <CardTitle>Zero Retention</CardTitle>
            <CardDescription>Privacy by design.</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-muted-foreground">
            We use API-level integrations with &quot;Zero Retention&quot; policies where possible. Your prompts are used for inference, not for training parent models.
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
            In the <strong>Settings &gt; Privacy</strong> section, you can export your entire local dataset, delete your profile, or toggle specific cloud providers on/off to suit your internal compliance requirements.
          </p>
        </div>
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 blur-[100px] pointer-events-none" />
      </section>

      <footer className="text-center text-muted-foreground text-sm py-8">
        <p>&copy; 2026 DataLogicEngine. Certified Cloud-Hybrid Compliance Tier 1.</p>
      </footer>
    </div>
  );
}

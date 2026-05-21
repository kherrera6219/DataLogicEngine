'use client';

import React from 'react';
import Link from 'next/link';
import { ShieldAlert, Info, AlertTriangle, CheckCircle, ExternalLink } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

export default function AILimitationsPage() {
  return (
    <div className="container mx-auto py-12 px-4 max-w-4xl space-y-12">
      <header className="space-y-4 text-center">
        <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">AI Transparency & Limitations</h1>
        <p className="text-xl text-muted-foreground">
          Understanding how DataLogicEngine utilizes Artificial Intelligence and the boundaries of this technology.
        </p>
      </header>

      <Alert variant="destructive" className="bg-destructive/10 border-destructive/20 text-destructive-foreground dark:text-destructive">
        <ShieldAlert className="h-5 w-5" />
        <AlertTitle className="font-bold">Crucial Notice</AlertTitle>
        <AlertDescription>
          DataLogicEngine is an augmented reasoning system. It is NOT a substitute for professional human judgment, legal advice, or medical diagnosis. Always verify critical implementation details.
        </AlertDescription>
      </Alert>

      <section className="space-y-6">
        <div className="flex items-center gap-2">
          <Info className="text-blue-500 h-6 w-6" />
          <h2 className="text-2xl font-bold">The Nature of Our AI</h2>
        </div>
        <p className="text-lg leading-relaxed">
          DataLogicEngine can route configured requests through multiple Large Language Model (LLM) providers. These systems operate from probabilistic patterns and retrieved context rather than guaranteed internal truth.
        </p>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card className="bg-background/50 backdrop-blur-sm border-premium">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="text-yellow-500 h-5 w-5" />
                Hallucinations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                AI may confidently generate facts, names, or code snippets that do not exist or are factually incorrect. This is inherent to the way transformers predict the next token.
              </p>
            </CardContent>
          </Card>

          <Card className="bg-background/50 backdrop-blur-sm border-premium">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShieldAlert className="text-red-500 h-5 w-5" />
                Inherent Bias
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Training data may contain human biases. The AI may reflect these biases in its reasoning. DataLogicEngine includes prompt and output controls, but those controls do not eliminate this risk.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="space-y-6">
        <h2 className="text-2xl font-bold">Our AI Providers</h2>
        <p className="text-muted-foreground">
          Depending on your settings and available credentials, requests may be routed to configured third-party providers:
        </p>
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { name: "OpenAI", models: "Configured OpenAI models" },
            { name: "Anthropic", models: "Configured Claude models" },
            { name: "Google Gemini / Vertex AI", models: "Configured Gemini models" },
            { name: "Microsoft Azure OpenAI", models: "Configured Azure OpenAI deployments" }
          ].map(p => (
            <li key={p.name} className="flex items-center gap-3 p-4 rounded-xl bg-muted/50 border border-border">
              <CheckCircle className="text-green-500 h-5 w-5" />
              <div>
                <span className="font-bold block">{p.name}</span>
                <span className="text-xs text-muted-foreground">{p.models}</span>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <section className="p-8 rounded-[2rem] bg-blue-600/5 border border-blue-500/10 space-y-4">
        <h2 className="text-2xl font-bold">Risk Mitigation: Our Truth Engine</h2>
        <p className="leading-relaxed">
          DataLogicEngine can add trace metadata, evidence context, and multi-perspective review steps around AI output. These controls are designed to make review easier; they do not certify that an answer is complete or correct.
        </p>
        <div className="flex justify-end">
          <Link href="/about" className="inline-flex items-center gap-2 text-blue-500 font-bold hover:underline">
            Read technical whitepaper <ExternalLink className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <footer className="text-center pt-8 border-t border-border">
        <p className="text-sm text-muted-foreground">
          Last Updated: May 2026 | AI output should be reviewed before operational, legal, medical, financial, or safety-critical use.
        </p>
      </footer>
    </div>
  );
}

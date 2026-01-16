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
          DataLogicEngine acts as a <strong>17-Dimensional Gateway</strong> to multiple Large Language Models (LLMs). While these models are highly capable, they operate based on probabilistic patterns rather than absolute internal truth.
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
                Training data may contain human biases. The AI may inadvertently reflect these biases in its reasoning, although we apply KA-61 adversarial filters to mitigate this.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="space-y-6">
        <h2 className="text-2xl font-bold">Our AI Providers</h2>
        <p className="text-muted-foreground">
          Depending on your settings and the task complexity, we route queries to various industry-standard providers:
        </p>
        <ul className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { name: "OpenAI", models: "GPT-4o, o1" },
            { name: "Anthropic", models: "Claude 3.5 Sonnet" },
            { name: "Google Cloud", models: "Gemini 1.5 Pro" },
            { name: "Microsoft Azure", models: "Enterprise GPT instances" }
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
          To combat AI limitations, the <strong>DataLogicEngine Truth Engine</strong> applies systematic deconfliction across multiple personas. This &quot;Quad-Persona&quot; approach reduces individual model error by requiring consensus across different reasoning vectors.
        </p>
        <div className="flex justify-end">
          <Link href="/about" className="inline-flex items-center gap-2 text-blue-500 font-bold hover:underline">
            Read technical whitepaper <ExternalLink className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <footer className="text-center pt-8 border-t border-border">
        <p className="text-sm text-muted-foreground">
          Last Updated: January 2026 | Compliant with MS-A10 Store Standards
        </p>
      </footer>
    </div>
  );
}

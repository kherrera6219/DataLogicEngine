'use client';

import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const algos = [
  "AoT (Algorithm of Thought)", "ToT (Tree of Thought)", "GAP (Gap Analysis)", "VALID (Input Validation)",
  "QCLASS (Query Classification)", "PLAN (Deep Planning)", "RECURSE (Recursive Control)", "CRITIQUE (Self-Critique)",
  "EVID (Evidence Validation)", "BIAS-DETECT (Bias Detection)", "MODEL (Analytical Modeling)", "PERSONA (Persona Sim)",
  "P-WEIGHT (Persona Weighting)", "CONF (Confidence Scoring)", "TIME (Temporal Reasoning)", "REGMAP (Regulatory Mapping)",
  "GEO (Spatial Mapping)", "PROV (Provenance Tracking)", "SYNTH (Knowledge Synthesis)"
];

export default function AboutPage() {
  const productVersion = process.env.NEXT_PUBLIC_APP_VERSION ?? "unavailable";
  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8">
      <div className="container mx-auto max-w-5xl">
        <header className="mb-12 text-center">
           <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">About DataLogicEngine</h1>
           <p className="text-xl text-gray-700 dark:text-gray-300 max-w-2xl mx-auto">
             A local-first knowledge graph workspace for traceable AI-assisted analysis, internal app-owned databases, and provider usage inspection.
           </p>
           <p className="mt-3 text-sm text-gray-600 dark:text-gray-400">
             Product version {productVersion}
           </p>
        </header>

        <section className="mb-12">
            <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">Core Architecture</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                   <CardHeader>
                      <CardTitle>Universal Knowledge Graph</CardTitle>
                   </CardHeader>
                   <CardContent className="text-gray-600 dark:text-gray-300">
                      The foundation of the system. A hyper-dimensional graph database storing facts across 6 primary pillars (Technology, Healthcare, Finance, etc.) connected by complex relationship types.
                   </CardContent>
                </Card>
                <Card>
                   <CardHeader>
                      <CardTitle>Truth Engine & KAs</CardTitle>
                   </CardHeader>
                   <CardContent className="text-gray-600 dark:text-gray-300">
                      More than 100 specialized Knowledge Algorithms (KAs) support distributed reasoning, validation, confidence scoring, provenance tracking, and provider-aware analysis.
                   </CardContent>
                </Card>
                <Card>
                   <CardHeader>
                      <CardTitle>LLM Gateway</CardTitle>
                   </CardHeader>
                   <CardContent className="text-gray-600 dark:text-gray-300">
                      A governed interface for the supported OpenAI and Google providers, with bounded calls, cancellation, trace metadata, privacy disclosures, and local usage inspection.
                   </CardContent>
                </Card>
            </div>
        </section>

        <section>
            <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">Knowledge Algorithm Registry</h2>
            <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6">
                <div className="flex flex-wrap gap-2">
                   {algos.map((algo) => (
                      <Badge key={algo} variant="secondary" className="px-3 py-1 text-sm">
                         {algo}
                      </Badge>
                   ))}
                   <Badge variant="outline" className="px-3 py-1 text-sm">+ more validated KAs</Badge>
                </div>
            </div>
        </section>
        <section className="mb-12">
            <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">Application Transparency</h2>
            <Card className="border-blue-100 dark:border-blue-900 bg-blue-50/50 dark:bg-blue-900/10">
                <CardContent className="pt-6">
                    <div className="flex flex-col md:flex-row gap-6 items-start">
                        <div className="flex-1 space-y-4">
                            <h3 className="font-bold text-lg text-blue-900 dark:text-blue-300">Local-First With Configured Cloud AI</h3>
                            <p className="text-blue-900 dark:text-blue-200 text-sm leading-relaxed">
                                The Windows desktop build uses local Windows identity and local app storage. AI reasoning features require internet access and may send prompts and selected context to the provider you configure.
                            </p>
                            <div className="flex flex-wrap gap-2 text-xs font-semibold text-blue-700 dark:text-blue-400">
                                <span className="bg-white dark:bg-blue-950 px-2 py-1 rounded border border-blue-200 dark:border-blue-800">Local Windows Identity</span>
                                <span className="bg-white dark:bg-blue-950 px-2 py-1 rounded border border-blue-200 dark:border-blue-800">Provider-Specific Terms</span>
                                <span className="bg-white dark:bg-blue-950 px-2 py-1 rounded border border-blue-200 dark:border-blue-800">User-Controlled AI Processing</span>
                            </div>
                        </div>
                        <div className="flex flex-col gap-2 w-full md:w-auto">
                           <Link href="/legal/privacy" className="inline-flex items-center justify-center px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors">
                               View Privacy Policy
                           </Link>
                           <Link href="/about/ai-limitations" className="inline-flex items-center justify-center px-4 py-2 rounded-md bg-white dark:bg-transparent border border-gray-200 dark:border-gray-700 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                               AI Limitations
                           </Link>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </section>
      </div>
    </main>
  );
}

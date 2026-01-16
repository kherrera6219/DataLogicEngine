'use client';

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
  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8">
      <div className="container mx-auto max-w-5xl">
        <header className="mb-12 text-center">
           <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">About DataLogicEngine</h1>
           <p className="text-xl text-gray-500 max-w-2xl mx-auto">
             An advanced Universal Knowledge Graph (UKG) system powered by 17-axis reasoning and 114 specialized Knowledge Algorithms.
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
                      114 specialized Knowledge Algorithms (KAs) act as the &quot;brain&quot;. From <span className="font-mono text-sm bg-gray-100 dark:bg-gray-800 px-1 rounded">KA-001 Algorithm of Thought</span> to <span className="font-mono text-sm bg-gray-100 dark:bg-gray-800 px-1 rounded">KA-114 Fractal Recursion</span>, these execute distributed reasoning.
                   </CardContent>
                </Card>
                <Card>
                   <CardHeader>
                      <CardTitle>LLM Gateway</CardTitle>
                   </CardHeader>
                   <CardContent className="text-gray-600 dark:text-gray-300">
                      A standardized interface allowing external Agents and LLMs (Claude, GPT-4) to query the UKG, execute algorithms, and retrieve deep reasoning traces via MCP.
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
                   <Badge variant="outline" className="px-3 py-1 text-sm">+ 95 more</Badge>
                </div>
            </div>
        </section>
        <section className="mb-12">
            <h2 className="text-2xl font-bold mb-6 text-gray-900 dark:text-white">Microsoft Store Compliance</h2>
            <Card className="border-blue-100 dark:border-blue-900 bg-blue-50/50 dark:bg-blue-900/10">
                <CardContent className="pt-6">
                    <div className="flex flex-col md:flex-row gap-6 items-start">
                        <div className="flex-1 space-y-4">
                            <h3 className="font-bold text-lg text-blue-900 dark:text-blue-300">Certified Secure & Transparent</h3>
                            <p className="text-blue-800/80 dark:text-blue-200/80 text-sm leading-relaxed">
                                DataLogicEngine is built to strict enterprise standards. We provide full transparency on AI usage, cloud dependencies, and data handling.
                            </p>
                            <div className="flex flex-wrap gap-2 text-xs font-semibold text-blue-700 dark:text-blue-400">
                                <span className="bg-white dark:bg-blue-950 px-2 py-1 rounded border border-blue-200 dark:border-blue-800">KA-61 Adversarial Shield</span>
                                <span className="bg-white dark:bg-blue-950 px-2 py-1 rounded border border-blue-200 dark:border-blue-800">ISO 27001 Aligned</span>
                                <span className="bg-white dark:bg-blue-950 px-2 py-1 rounded border border-blue-200 dark:border-blue-800">Zero-Retention Mode</span>
                            </div>
                        </div>
                        <div className="flex flex-col gap-2 w-full md:w-auto">
                           <a href="/legal/privacy" className="inline-flex items-center justify-center px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors">
                               View Privacy Policy
                           </a>
                           <a href="/about/ai-limitations" className="inline-flex items-center justify-center px-4 py-2 rounded-md bg-white dark:bg-transparent border border-gray-200 dark:border-gray-700 text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                               AI Limitations
                           </a>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </section>
      </div>
    </main>
  );
}

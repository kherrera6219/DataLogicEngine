'use client';

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

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
                      114 specialized Knowledge Algorithms (KAs) act as the "brain". From <span className="font-mono text-sm bg-gray-100 dark:bg-gray-800 px-1 rounded">KA-001 Algorithm of Thought</span> to <span className="font-mono text-sm bg-gray-100 dark:bg-gray-800 px-1 rounded">KA-114 Fractal Recursion</span>, these execute distributed reasoning.
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
                   {[
                      "AoT (Algorithm of Thought)", "ToT (Tree of Thought)", "GAP (Gap Analysis)", "VALID (Input Validation)",
                      "QCLASS (Query Classification)", "PLAN (Deep Planning)", "RECURSE (Recursive Control)", "CRITIQUE (Self-Critique)",
                      "EVID (Evidence Validation)", "BIAS-DETECT (Bias Detection)", "MODEL (Analytical Modeling)", "PERSONA (Persona Sim)",
                      "P-WEIGHT (Persona Weighting)", "CONF (Confidence Scoring)", "TIME (Temporal Reasoning)", "REGMAP (Regulatory Mapping)",
                      "GEO (Spatial Mapping)", "PROV (Provenance Tracking)", "SYNTH (Knowledge Synthesis)"
                   ].map((algo) => (
                      <Badge key={algo} variant="secondary" className="px-3 py-1 text-sm">
                         {algo}
                      </Badge>
                   ))}
                   <Badge variant="outline" className="px-3 py-1 text-sm">+ 95 more</Badge>
                </div>
            </div>
        </section>
      </div>
    </main>
  );
}

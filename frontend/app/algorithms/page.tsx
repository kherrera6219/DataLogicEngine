'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const algorithms = [
  { id: "KA-001", name: "Algorithm of Thought", type: "Reasoning", desc: "Linear reasoning integrity check.", tier: "Core" },
  { id: "KA-002", name: "Tree of Thought", type: "Reasoning", desc: "Branching scenario exploration.", tier: "Core" },
  { id: "KA-012", name: "Graph Isomorphism", type: "Structure", desc: "Identifies structural similarity in subgraphs.", tier: "Advanced" },
  { id: "KA-042", name: "Causal Inference", type: "Logic", desc: "Determines cause-effect relationships.", tier: "Advanced" },
  { id: "KA-099", name: "Persona Simulation", type: "Simulation", desc: "Simulates actor behavior based on profile.", tier: "Enterprise" },
  { id: "KA-103", name: "Regulatory Mapping", type: "Compliance", desc: "Maps actions to ISO/GDPR controls.", tier: "Enterprise" },
  { id: "KA-114", name: "Fractal Recursion", type: "Meta", desc: "Self-similar pattern detection at scale.", tier: "Experimental" },
];

export default function AlgorithmsPage() {
  return (
    <main className="min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8">
      <div className="container mx-auto max-w-7xl">
        <header className="mb-8 flex flex-col md:flex-row justify-between items-center gap-4">
          <div>
             <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Algorithm Registry</h1>
             <p className="text-gray-500">Catalog of 114 Active Knowledge Algorithms.</p>
          </div>
          <div className="flex w-full md:w-auto gap-2">
             <Input placeholder="Search algorithms..." className="w-full md:w-64" />
             <Button>Search</Button>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
           {algorithms.map((algo) => (
              <Card key={algo.id} className="hover:border-blue-500 transition-colors cursor-pointer group">
                 <CardHeader>
                    <div className="flex justify-between items-start mb-2">
                       <Badge variant="outline" className="font-mono text-xs">{algo.id}</Badge>
                       <Badge variant={
                          algo.tier === 'Core' ? 'default' : 
                          algo.tier === 'Enterprise' ? 'secondary' : 'outline'
                       }>{algo.tier}</Badge>
                    </div>
                    <CardTitle className="text-lg group-hover:text-blue-600 transition-colors">{algo.name}</CardTitle>
                    <CardDescription>{algo.type}</CardDescription>
                 </CardHeader>
                 <CardContent>
                    <p className="text-sm text-gray-600 dark:text-gray-300">
                       {algo.desc}
                    </p>
                 </CardContent>
              </Card>
           ))}
           {/* Placeholder for the rest */}
           <Card className="flex items-center justify-center p-6 border-dashed bg-gray-50/50 dark:bg-gray-900/50">
               <p className="text-gray-400 text-sm max-w-[200px] text-center">
                  + 107 more algorithms indexed in the registry...
               </p>
           </Card>
        </div>
      </div>
    </main>
  );
}

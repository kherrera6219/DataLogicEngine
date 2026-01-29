'use client';

import Link from "next/link";
import { PageLayout } from "@/components/ui/page-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const truthEvents = [
  { id: "TE-8821", statement: "Inflation correlates with localized weather patterns", verdict: "False", confidence: 99.2, ka: "KA-042 (Causal)" },
  { id: "TE-8820", statement: "Supply chain node [SC-202] is critical failure point", verdict: "True", confidence: 88.5, ka: "KA-012 (Graph)" },
  { id: "TE-8819", statement: "User [U-992] exhibits anomalous behavior pattern", verdict: "Uncertain", confidence: 45.0, ka: "KA-099 (Persona)" },
];

export default function TruthEnginePage() {
  return (
    <PageLayout
      title="Truth Engine"
      description="Real-time validation of logic and causality across the Knowledge Graph."
      breadcrumbs={[{ label: "Dashboard", href: "/dashboard" }, { label: "Truth Engine" }]}
    >
      <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
           <Card className="fluent-acrylic border-none bg-blue-600/90 text-white shadow-[0_8px_32px_rgba(37,99,235,0.3)] overflow-hidden relative group">
              <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent pointer-events-none" />
              <CardHeader className="relative z-10">
                 <CardTitle className="text-white/90 text-sm font-bold tracking-wider uppercase">Truth Score</CardTitle>
                 <CardDescription className="text-blue-100/70">Global system coherence audit.</CardDescription>
              </CardHeader>
              <CardContent className="relative z-10">
                 <div className="text-6xl font-bold mb-4 tracking-tighter">94.8%</div>
                 <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-white/20 w-fit text-xs font-bold backdrop-blur-md border border-white/10">
                    <span className="h-1.5 w-1.5 rounded-full bg-green-400 shadow-[0_0_8px_rgba(74,222,128,0.8)]"></span>
                    HIGH COHERENCE
                 </div>
              </CardContent>
           </Card>
           
           <Card className="fluent-acrylic border-white/10 shadow-xl hover:bg-white/5 transition-all">
              <CardHeader>
                 <CardTitle className="text-gray-100 text-sm font-bold tracking-wider uppercase">Active Validators</CardTitle>
                 <CardDescription className="text-gray-500">Algorithms currently processing claims.</CardDescription>
              </CardHeader>
              <CardContent>
                 <div className="text-4xl font-bold mb-2 text-white">18</div>
                 <div className="flex items-center gap-2 text-xs text-blue-400 font-mono">
                    <span className="animate-pulse">●</span>
                    1,240 claims / sec
                 </div>
              </CardContent>
           </Card>

           <Card className="fluent-acrylic border-white/10 shadow-xl hover:bg-white/5 transition-all">
              <CardHeader>
                 <CardTitle className="text-gray-100 text-sm font-bold tracking-wider uppercase">Conflict Rate</CardTitle>
                 <CardDescription className="text-gray-500">Detected logical inconsistencies.</CardDescription>
              </CardHeader>
              <CardContent>
                 <div className="text-4xl font-bold mb-2 text-yellow-500">0.4%</div>
                 <div className="flex items-center gap-2 text-xs text-gray-500 font-mono">
                    OPTIMAL_THRESHOLD_OK
                 </div>
              </CardContent>
           </Card>
        </div>

        <Card className="fluent-acrylic border-white/10 overflow-hidden shadow-2xl">
           <CardHeader className="border-b border-white/5 bg-white/5">
              <CardTitle className="text-gray-100">Validation Log</CardTitle>
              <CardDescription className="text-gray-500">Recent claim verifications executed by the engine.</CardDescription>
           </CardHeader>
           <CardContent className="p-0">
              <Table>
                 <TableHeader className="bg-white/5">
                    <TableRow className="hover:bg-transparent border-white/5">
                       <TableHead className="text-gray-400 font-bold text-xs uppercase tracking-wider">Event ID</TableHead>
                       <TableHead className="text-gray-400 font-bold text-xs uppercase tracking-wider">Statement / Claim</TableHead>
                       <TableHead className="text-gray-400 font-bold text-xs uppercase tracking-wider">KA Used</TableHead>
                       <TableHead className="text-gray-400 font-bold text-xs uppercase tracking-wider">Verdict</TableHead>
                       <TableHead className="text-right text-gray-400 font-bold text-xs uppercase tracking-wider">Confidence</TableHead>
                    </TableRow>
                 </TableHeader>
                 <TableBody>
                    {truthEvents.map((evt) => (
                       <TableRow key={evt.id} className="border-white/5 hover:bg-white/5 transition-colors group">
                          <TableCell className="font-mono text-[10px] text-gray-500">
                             <Link href={`/runs/view?id=${evt.id}`} className="text-blue-400 hover:text-blue-300 transition-colors">
                                {evt.id}
                             </Link>
                          </TableCell>
                          <TableCell className="font-medium text-gray-200">{evt.statement}</TableCell>
                          <TableCell className="text-xs text-gray-400 font-mono">{evt.ka}</TableCell>
                          <TableCell>
                             <Badge 
                                variant="outline"
                                className={cn(
                                   "px-2 py-0 h-5 text-[10px] font-bold border-none",
                                   evt.verdict === 'True' ? 'bg-green-500/20 text-green-400' : 
                                   evt.verdict === 'False' ? 'bg-red-500/20 text-red-400' : 'bg-gray-500/20 text-gray-400'
                                )}
                             >
                                {evt.verdict.toUpperCase()}
                             </Badge>
                          </TableCell>
                          <TableCell className="text-right font-mono text-xs text-blue-400 font-bold">{evt.confidence}%</TableCell>
                       </TableRow>
                    ))}
                 </TableBody>
              </Table>
           </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}

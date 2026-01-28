'use client';

import { PageLayout } from "@/components/ui/page-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

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
      breadcrumbs={[{ label: "Truth Engine" }]}
    >

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
           <Card className="bg-blue-600 text-white border-none">
              <CardHeader>
                 <CardTitle className="text-white">Truth Score</CardTitle>
                 <CardDescription className="text-blue-100">Global system coherence audit.</CardDescription>
              </CardHeader>
              <CardContent>
                 <div className="text-5xl font-bold mb-2">94.8%</div>
                 <Badge variant="secondary" className="bg-white/20 text-white hover:bg-white/30 border-none">
                    High Coherence
                 </Badge>
              </CardContent>
           </Card>
           
           <Card>
              <CardHeader>
                 <CardTitle>Active Validators</CardTitle>
                 <CardDescription>Algorithms currently processing claims.</CardDescription>
              </CardHeader>
              <CardContent>
                 <div className="text-4xl font-bold mb-2">18</div>
                 <p className="text-sm text-gray-500">Processing 1,240 claims/sec</p>
              </CardContent>
           </Card>

           <Card>
              <CardHeader>
                 <CardTitle>Conflict Rate</CardTitle>
                 <CardDescription>Detected logical inconsistencies.</CardDescription>
              </CardHeader>
              <CardContent>
                 <div className="text-4xl font-bold mb-2 text-yellow-600">0.4%</div>
                 <p className="text-sm text-gray-500">Below 1% threshold</p>
              </CardContent>
           </Card>
        </div>

        <Card>
           <CardHeader>
              <CardTitle>Validation Log</CardTitle>
              <CardDescription>Recent claim verifications executed by the engine.</CardDescription>
           </CardHeader>
           <CardContent>
              <Table>
                 <TableHeader>
                    <TableRow>
                       <TableHead>Event ID</TableHead>
                       <TableHead>Statement / Claim</TableHead>
                       <TableHead>KA Used</TableHead>
                       <TableHead>Verdict</TableHead>
                       <TableHead className="text-right">Confidence</TableHead>
                    </TableRow>
                 </TableHeader>
                 <TableBody>
                    {truthEvents.map((evt) => (
                       <TableRow key={evt.id}>
                          <TableCell className="font-mono text-xs">{evt.id}</TableCell>
                          <TableCell className="font-medium">{evt.statement}</TableCell>
                          <TableCell>{evt.ka}</TableCell>
                          <TableCell>
                             <Badge variant={
                                evt.verdict === 'True' ? 'success' : 
                                evt.verdict === 'False' ? 'destructive' : 'secondary'
                             }>
                                {evt.verdict}
                             </Badge>
                          </TableCell>
                          <TableCell className="text-right font-mono">{evt.confidence}%</TableCell>
                       </TableRow>
                    ))}
                 </TableBody>
              </Table>
           </CardContent>
        </Card>
    </PageLayout>
  );
}

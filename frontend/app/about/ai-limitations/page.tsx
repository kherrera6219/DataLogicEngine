
import { AlertTriangle, Info, CheckCircle, ShieldAlert } from 'lucide-react';
import Link from 'next/link';

export default function AILimitationsPage() {
  return (
    <div className="container max-w-4xl py-12 space-y-8">
      <div className="space-y-4">
        <h1 className="text-4xl font-bold tracking-tight">AI Limitations & Disclaimers</h1>
        <p className="text-xl text-muted-foreground">
          Understanding the capabilities and constraints of the Artificial Intelligence powering DataLogicEngine.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="p-6 rounded-xl border bg-card text-card-foreground shadow-sm">
           <div className="flex items-center gap-3 mb-4">
             <div className="p-2 w-fit rounded-lg bg-orange-500/10 text-orange-500">
               <AlertTriangle className="h-6 w-6" />
             </div>
             <h3 className="font-semibold text-lg">Potential for Inaccuracy</h3>
           </div>
           <p className="text-sm text-muted-foreground leading-relaxed">
             AI models may occasionally produce incorrect or misleading information (&quot;hallucinations&quot;). 
             While our Truth Engine adds verification layers, the underlying models are probabilistic 
             and can make confident-sounding mistakes.
           </p>
        </div>

        <div className="p-6 rounded-xl border bg-card text-card-foreground shadow-sm">
           <div className="flex items-center gap-3 mb-4">
             <div className="p-2 w-fit rounded-lg bg-blue-500/10 text-blue-500">
               <Info className="h-6 w-6" />
             </div>
             <h3 className="font-semibold text-lg">Knowledge Cutoffs</h3>
           </div>
           <p className="text-sm text-muted-foreground leading-relaxed">
             The base AI models have knowledge cutoffs and may not know about very recent events 
             unless explicitly provided via our real-time retrieval tools.
           </p>
        </div>
      </div>

      <div className="space-y-6">
        <h2 className="text-2xl font-bold border-b pb-2">When to Verify AI Outputs</h2>
        <div className="grid gap-4">
            <div className="flex gap-4 p-4 rounded-lg bg-secondary/50 border border-border/50">
              <ShieldAlert className="h-6 w-6 text-red-500 shrink-0 mt-1" />
              <div>
                <h4 className="font-medium text-foreground">Critical Decisions</h4>
                <p className="text-sm text-muted-foreground">
                   Do not rely solely on AI for medical, legal, financial, or safety-critical decisions. 
                   Always consult a qualified professional.
                </p>
              </div>
            </div>
            
            <div className="flex gap-4 p-4 rounded-lg bg-secondary/50 border border-border/50">
               <CheckCircle className="h-6 w-6 text-green-500 shrink-0 mt-1" />
               <div>
                 <h4 className="font-medium text-foreground">Verification Recommended</h4>
                 <p className="text-sm text-muted-foreground">
                    For code generation, factual reporting, or compliance tasks, use the "Trace" feature 
                    to audit the AI's reasoning steps and source citations.
                 </p>
               </div>
            </div>
        </div>
      </div>

      <div className="space-y-6">
         <h2 className="text-2xl font-bold border-b pb-2">Our Risk Mitigation Features</h2>
         <ul className="grid gap-3 md:grid-cols-2">
            <li className="flex items-start gap-2">
               <span className="text-blue-500 mt-1">•</span>
               <span className="text-sm text-muted-foreground">
                 <strong>Truth Engine:</strong> Cross-references claims against verified knowledge bases.
               </span>
            </li>
            <li className="flex items-start gap-2">
               <span className="text-blue-500 mt-1">•</span>
               <span className="text-sm text-muted-foreground">
                 <strong>Audit Trails:</strong> Every AI action is logged for accountability (EU AI Act Article 53).
               </span>
            </li>
            <li className="flex items-start gap-2">
               <span className="text-blue-500 mt-1">•</span>
               <span className="text-sm text-muted-foreground">
                 <strong>Multi-Persona Consensus:</strong> Uses multiple viewpoints to reduce individual bias.
               </span>
            </li>
            <li className="flex items-start gap-2">
               <span className="text-blue-500 mt-1">•</span>
               <span className="text-sm text-muted-foreground">
                 <strong>Adversarial Shields:</strong> Dedicated layers to block harmful inputs.
               </span>
            </li>
         </ul>
      </div>
      
      <div className="pt-8 border-t flex justify-between items-center text-sm text-muted-foreground">
         <p>Last Updated: January 16, 2026</p>
         <Link href="/" className="hover:underline">Return to Home</Link>
      </div>
    </div>
  );
}

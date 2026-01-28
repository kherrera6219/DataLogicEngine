import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  CheckCircle2, Shield, 
  Activity, Gavel, Building, Stethoscope,
  Download, Share2, Users
} from "lucide-react";

export function DetailedResponseView() {
  const [activePersona, setActivePersona] = useState<string | null>(null);

  const personas = [
    {
      id: "p1",
      name: "Knowledge Expert",
      role: "Healthcare Systems & Law",
      icon: <Stethoscope className="h-4 w-4 text-blue-400" />,
      confidence: 99.7,
      contribution: "Identified AES-256 & TLS 1.3 requirements. Noted 7-year audit log retention."
    },
    {
      id: "p2",
      name: "Sector Specialist",
      role: "IT Ops & Cloud Arch",
      icon: <Building className="h-4 w-4 text-orange-400" />,
      confidence: 99.4,
      contribution: "Emphasized BAAs and data residency. Specified RTO < 4 hours."
    },
    {
      id: "p3",
      name: "Regulatory Advisor",
      role: "HIPAA Attorney",
      icon: <Gavel className="h-4 w-4 text-purple-400" />,
      confidence: 99.8,
      contribution: "Mapped 45 CFR § 164.308/312. Flagged HITECH & State laws."
    },
    {
      id: "p4",
      name: "Compliance Officer",
      role: "CISO & Auditor",
      icon: <Shield className="h-4 w-4 text-green-400" />,
      confidence: 99.5,
      contribution: "Validated SOC2/ISO alignment. Created 14-point risk checklist."
    }
  ];

  const metrics = [
    { label: "Factual Acc.", value: "99.8%", status: "pass", detail: "Verified vs 23 sources" },
    { label: "Legal Validity", value: "99.6%", status: "pass", detail: "8 regulatory codes" },
    { label: "Completeness", value: "98.4%", status: "pass", detail: "All aspects covered" },
    { label: "Consistency", value: "99.9%", status: "pass", detail: "Zero contradictions" },
    { label: "Bias Score", value: "0.02", status: "pass", detail: "Threshold < 0.05" },
    { label: "Safety Check", value: "PASS", status: "pass", detail: "No harmful content" },
  ];

  return (
    <div className="space-y-6 mt-4">
       {/* 🔬 VALIDATION METRICS */}
       <div className="bg-black/30 border border-white/10 rounded-lg p-4">
          <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
             <Activity className="h-3 w-3" /> Validation Metrics
          </h3>
          <div className="grid grid-cols-3 gap-3">
             {metrics.map((m, i) => (
                <div key={i} className="bg-white/5 border border-white/5 p-2 rounded flex flex-col">
                   <div className="flex justify-between items-start mb-1">
                      <span className="text-[10px] text-gray-400 uppercase">{m.label}</span>
                      {m.status === 'pass' && <CheckCircle2 className="h-3 w-3 text-green-500" />}
                   </div>
                   <div className="text-lg font-bold text-white leading-none mb-1">{m.value}</div>
                   <div className="text-[10px] text-gray-500 truncate">{m.detail}</div>
                </div>
             ))}
          </div>
       </div>

       {/* 🎭 QUAD PERSONA ANALYSIS */}
       <div className="border border-white/10 rounded-lg overflow-hidden">
          <div className="bg-white/5 p-3 border-b border-white/10 flex justify-between items-center">
             <h3 className="text-xs font-bold text-gray-300 uppercase tracking-wider flex items-center gap-2">
                <Users className="h-3 w-3 text-blue-400" /> Quad Persona Analysis
             </h3>
             <Badge variant="outline" className="text-[10px] h-5 border-blue-500/30 text-blue-400">Consensus: 98.7%</Badge>
          </div>
          
          <div className="divide-y divide-white/10">
             {personas.map(persona => (
                <div 
                  key={persona.id} 
                  className="p-3 bg-black/20 hover:bg-white/5 transition-colors cursor-pointer group"
                >
                   <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                         <div className="p-1 rounded bg-white/5 border border-white/10">{persona.icon}</div>
                         <div>
                            <div className="text-sm font-bold text-gray-200 group-hover:text-white">{persona.name}</div>
                            <div className="text-[10px] text-gray-500">{persona.role}</div>
                         </div>
                      </div>
                      <div className="text-right">
                         <div className="text-xs font-bold text-green-400">{persona.confidence}%</div>
                         <div className="text-[9px] text-gray-600 uppercase">Confidence</div>
                      </div>
                   </div>
                   <p className="text-xs text-gray-400 pl-9 border-l-2 border-white/10 ml-2">
                      {persona.contribution}
                   </p>
                </div>
             ))}
          </div>
       </div>

       {/* Actions */}
       <div className="flex justify-end gap-2 pt-2">
          <Button variant="ghost" size="sm" className="h-7 text-xs text-gray-400 hover:text-white gap-2">
             <Download className="h-3 w-3" /> Report
          </Button>
          <Button variant="ghost" size="sm" className="h-7 text-xs text-gray-400 hover:text-white gap-2">
             <Share2 className="h-3 w-3" /> Share
          </Button>
       </div>
    </div>
  );
}

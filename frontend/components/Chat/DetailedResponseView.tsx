import React from 'react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  Shield,
  Activity,
  Gavel,
  Building,
  Stethoscope,
  Download,
  Share2,
  Users
} from "lucide-react";
import { ChatMessage, PersonaOutput, ValidationMetric } from './types';

interface DetailedResponseViewProps {
  message: ChatMessage;
}

function toPercent(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return value <= 1 ? value * 100 : value;
}

function personaIcon(persona: PersonaOutput): React.ReactNode {
  const descriptor = `${persona.name} ${persona.role}`.toLowerCase();
  if (descriptor.includes('health') || descriptor.includes('medical')) {
    return <Stethoscope className="h-4 w-4 text-blue-400" />;
  }
  if (descriptor.includes('regulatory') || descriptor.includes('legal')) {
    return <Gavel className="h-4 w-4 text-purple-400" />;
  }
  if (descriptor.includes('sector') || descriptor.includes('operations') || descriptor.includes('cloud')) {
    return <Building className="h-4 w-4 text-orange-400" />;
  }
  if (descriptor.includes('compliance') || descriptor.includes('security')) {
    return <Shield className="h-4 w-4 text-green-400" />;
  }
  return <Users className="h-4 w-4 text-blue-400" />;
}

function metricLabel(metric: ValidationMetric): string {
  return metric.name
    .replace(/_/g, ' ')
    .toLowerCase()
    .split(' ')
    .map((segment) => segment.charAt(0).toUpperCase() + segment.substring(1))
    .join(' ');
}

function personaAriaLabel(persona: PersonaOutput): string {
  return `${persona.name}, ${persona.role}, confidence ${toPercent(persona.confidence).toFixed(1)} percent`;
}

export function DetailedResponseView({ message }: DetailedResponseViewProps) {
  const personas = message.personas || [];
  const metrics = message.metrics || [];
  const consensus = personas.length
    ? personas.reduce((sum, persona) => sum + toPercent(persona.confidence), 0) / personas.length
    : null;

  if (!personas.length && !metrics.length) {
    return (
      <div className="mt-4 rounded-lg border border-slate-200/80 dark:border-white/10 bg-slate-50 dark:bg-black/20 p-3 text-xs text-slate-600 dark:text-gray-400">
        No validation telemetry is available for this response yet.
      </div>
    );
  }

  return (
    <div className="space-y-6 mt-4">
      {metrics.length > 0 && (
        <section
          className="bg-white/70 dark:bg-black/30 border border-slate-200 dark:border-white/10 rounded-lg p-4"
          role="region"
          aria-label="Validation metrics"
        >
          <h3 className="text-xs font-bold text-slate-500 dark:text-gray-500 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Activity className="h-3 w-3" aria-hidden="true" /> Validation Metrics
          </h3>
          <div className="grid grid-cols-3 gap-3" role="list" aria-label="Validation metric scores">
            {metrics.map((metric) => (
              <div
                key={metric.name}
                className="bg-white/70 dark:bg-white/5 border border-slate-200 dark:border-white/5 p-2 rounded flex flex-col"
                role="listitem"
              >
                <div className="flex justify-between items-start mb-1">
                  <span className="text-[10px] text-slate-600 dark:text-gray-400 uppercase">{metricLabel(metric)}</span>
                  {metric.status === 'pass' && <CheckCircle2 className="h-3 w-3 text-green-500" aria-hidden="true" />}
                </div>
                <div
                  className="text-lg font-bold text-slate-900 dark:text-white leading-none mb-1"
                  role="meter"
                  aria-label={metricLabel(metric)}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={Math.round(toPercent(metric.score))}
                >
                  {toPercent(metric.score).toFixed(1)}%
                </div>
                <div className="text-[10px] text-slate-500 dark:text-gray-500 truncate">{metric.details}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {personas.length > 0 && (
        <section
          className="border border-slate-200 dark:border-white/10 rounded-lg overflow-hidden"
          role="region"
          aria-label="Persona analysis"
        >
          <div className="bg-white/70 dark:bg-white/5 p-3 border-b border-slate-200 dark:border-white/10 flex justify-between items-center">
            <h3 className="text-xs font-bold text-slate-700 dark:text-gray-300 uppercase tracking-wider flex items-center gap-2">
              <Users className="h-3 w-3 text-blue-400" aria-hidden="true" /> Persona Analysis
            </h3>
            {consensus !== null && (
              <Badge variant="outline" className="text-[10px] h-5 border-blue-500/30 text-blue-400">
                Consensus: {consensus.toFixed(1)}%
              </Badge>
            )}
          </div>

          <div className="divide-y divide-slate-200 dark:divide-white/10" role="list" aria-label="Persona contributions">
            {personas.map((persona) => (
              <div
                key={persona.id}
                className="p-3 bg-slate-50 dark:bg-black/20 hover:bg-slate-100 dark:hover:bg-white/5 transition-colors group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/60"
                role="listitem"
                tabIndex={0}
                aria-label={personaAriaLabel(persona)}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className="p-1 rounded bg-white/70 dark:bg-white/5 border border-slate-200 dark:border-white/10">{personaIcon(persona)}</div>
                    <div>
                      <div className="text-sm font-bold text-slate-900 dark:text-gray-200 group-hover:text-slate-950 dark:group-hover:text-white">{persona.name}</div>
                      <div className="text-[10px] text-slate-500 dark:text-gray-500">{persona.role}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div
                      className="text-xs font-bold text-green-400"
                      role="meter"
                      aria-label={`${persona.name} confidence`}
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={Math.round(toPercent(persona.confidence))}
                    >
                      {toPercent(persona.confidence).toFixed(1)}%
                    </div>
                    <div className="text-[9px] text-slate-500 dark:text-gray-600 uppercase">Confidence</div>
                  </div>
                </div>
                <p className="text-xs text-slate-600 dark:text-gray-400 pl-9 border-l-2 border-slate-300 dark:border-white/10 ml-2">
                  {persona.contribution || 'No contribution details were captured for this persona.'}
                </p>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="ghost" size="sm" className="h-7 text-xs text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white gap-2" aria-label="Download validation report">
          <Download className="h-3 w-3" aria-hidden="true" /> Report
        </Button>
        <Button variant="ghost" size="sm" className="h-7 text-xs text-slate-600 dark:text-gray-400 hover:text-slate-900 dark:hover:text-white gap-2" aria-label="Share validation details">
          <Share2 className="h-3 w-3" aria-hidden="true" /> Share
        </Button>
      </div>
    </div>
  );
}

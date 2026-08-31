import React, { useRef, useState } from 'react';
import { CheckCircle2, Clock, PlayCircle, ZoomIn } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { TracePipeline, TraceStep } from './types';

interface TraceVisualizerProps {
  trace?: TracePipeline | null;
  hasExecutedQuery?: boolean;
}

type TraceView = 'tree' | 'timeline';

function statusIcon(step: TraceStep) {
  if (step.status === 'completed') return <CheckCircle2 className="h-4 w-4 text-green-600" aria-hidden="true" />;
  if (step.status === 'processing') return <PlayCircle className="h-4 w-4 text-blue-600" aria-hidden="true" />;
  return <Clock className="h-4 w-4 text-slate-500" aria-hidden="true" />;
}

export function TraceVisualizer({ trace, hasExecutedQuery = false }: TraceVisualizerProps) {
  const steps = trace?.steps || [];
  const [view, setView] = useState<TraceView>('tree');
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const tabRefs = useRef<Record<TraceView, HTMLButtonElement | null>>({ tree: null, timeline: null });
  const effectiveSelectedStepId = selectedStepId && steps.some((step) => step.id === selectedStepId)
    ? selectedStepId
    : trace?.currentStepId || steps[0]?.id || null;

  const selectView = (next: TraceView) => {
    setView(next);
    tabRefs.current[next]?.focus();
  };

  const handleTabKey = (event: React.KeyboardEvent<HTMLButtonElement>) => {
    if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') {
      event.preventDefault();
      selectView(view === 'tree' ? 'timeline' : 'tree');
    } else if (event.key === 'Home') {
      event.preventDefault();
      selectView('tree');
    } else if (event.key === 'End') {
      event.preventDefault();
      selectView('timeline');
    }
  };

  const selected = steps.find((step) => step.id === effectiveSelectedStepId) || null;

  return (
    <Card className="border-slate-200 bg-white/80 dark:border-white/10 dark:bg-black/40">
      <CardHeader className="border-b border-slate-200 py-3 dark:border-white/10">
        <CardTitle className="flex items-center gap-2 text-sm font-bold">
          <ZoomIn className="h-4 w-4 text-blue-500" aria-hidden="true" />
          Interactive Trace Explorer
        </CardTitle>
        <div role="tablist" aria-label="Trace view" className="mt-3 flex gap-2">
          {(['tree', 'timeline'] as const).map((name) => (
            <button
              key={name}
              ref={(node) => { tabRefs.current[name] = node; }}
              type="button"
              role="tab"
              aria-selected={view === name}
              aria-controls={`trace-${name}-panel`}
              tabIndex={view === name ? 0 : -1}
              onClick={() => selectView(name)}
              onKeyDown={handleTabKey}
              className="min-h-10 rounded-lg border px-3 text-xs font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 aria-selected:border-blue-500 aria-selected:bg-blue-500/10 aria-selected:text-blue-700 dark:aria-selected:text-blue-300"
            >
              {name === 'tree' ? 'Tree view' : 'Timeline view'}
            </button>
          ))}
        </div>
      </CardHeader>
      <CardContent className="space-y-4 p-4">
        {steps.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-300/80 bg-slate-50/80 px-4 py-8 text-center text-xs text-slate-500 dark:border-white/10 dark:bg-black/20">
            {hasExecutedQuery ? 'No trace data returned for this query.' : 'Run a query to populate the trace timeline.'}
          </div>
        ) : (
          <>
            <div
              id={`trace-${view}-panel`}
              role="tabpanel"
              aria-label={view === 'tree' ? 'Tree view stages' : 'Timeline view stages'}
            >
              <ol
                role="list"
                aria-label="Trace stages"
                className="max-h-80 space-y-2 overflow-y-auto overscroll-contain pr-1"
              >
                {steps.map((step, index) => (
                  <li key={step.id} className="relative">
                    <button
                      type="button"
                      aria-expanded={effectiveSelectedStepId === step.id}
                      onClick={() => setSelectedStepId(step.id)}
                      className="flex min-h-11 w-full items-center gap-3 rounded-lg border border-slate-200 bg-white/70 px-3 py-2 text-left hover:bg-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 dark:border-white/10 dark:bg-white/5 dark:hover:bg-white/10"
                    >
                      {statusIcon(step)}
                      <span className="min-w-0 flex-1">
                        <span className="block text-xs font-medium text-slate-800 dark:text-slate-200">{step.name}</span>
                        <span className="block text-[11px] capitalize text-slate-500">
                          {view === 'tree' ? `Stage ${index + 1} · ${step.status}` : `${step.timestamp} · ${step.status}`}
                        </span>
                      </span>
                      <span className="shrink-0 font-mono text-[11px] text-slate-500">
                        {step.durationMs !== undefined ? `${step.durationMs}ms` : 'Not measured'}
                      </span>
                    </button>
                  </li>
                ))}
              </ol>
            </div>

            {selected && (
              <section className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-3" aria-label="Selected stage details">
                <h3 className="text-xs font-semibold">Selected stage details</h3>
                <dl className="mt-2 grid grid-cols-2 gap-2 text-xs">
                  <div><dt className="text-slate-500">Stage</dt><dd>{selected.name}</dd></div>
                  <div><dt className="text-slate-500">Status</dt><dd className="capitalize">{selected.status}</dd></div>
                  <div><dt className="text-slate-500">Timeline point</dt><dd>{selected.timestamp}</dd></div>
                  <div><dt className="text-slate-500">Duration</dt><dd>{selected.durationMs !== undefined ? `${selected.durationMs}ms` : 'Not measured'}</dd></div>
                </dl>
              </section>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}

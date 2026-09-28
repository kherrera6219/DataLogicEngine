import type { ConfidenceDisplay } from '@/lib/api/types';

interface ConfidenceDisplayCardProps {
  display?: ConfidenceDisplay | null;
  compact?: boolean;
}

function measuredPercent(display?: ConfidenceDisplay | null): string {
  if (display?.status !== 'measured' || typeof display.value !== 'number') {
    return 'Not measured';
  }
  const normalized = display.value <= 1 ? display.value * 100 : display.value;
  return `${normalized.toFixed(1)}%`;
}

export function ConfidenceDisplayCard({ display, compact = false }: ConfidenceDisplayCardProps) {
  const valueLabel = measuredPercent(display);
  const explanation = display?.explanation
    || 'The governed evidence-support formula did not produce a measurement for this run.';
  const statusLabel = display?.status === 'validation_failed'
    ? 'Validation failed'
    : display?.status === 'insufficient_evidence'
      ? 'Insufficient evidence'
      : display?.status === 'measured'
        ? 'Measured'
        : 'Not measured';

  return (
    <div className={`rounded-lg border border-slate-200 bg-white/70 dark:border-white/10 dark:bg-white/5 ${compact ? 'p-2' : 'p-3'}`}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-medium text-slate-600 dark:text-slate-300">Evidence support</span>
        <span className="font-semibold">{valueLabel}</span>
      </div>
      {statusLabel !== valueLabel && (
        <div className="mt-1 text-[11px] font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
          {statusLabel}
        </div>
      )}
      <p className="mt-1 text-xs text-slate-600 dark:text-slate-300">{explanation}</p>
      {display?.formula_version && (
        <div className="mt-1 font-mono text-[10px] text-slate-500 dark:text-slate-400">
          {display.formula_version}
        </div>
      )}
      {display?.missing_components?.length ? (
        <div className="mt-1 text-[10px] text-slate-500 dark:text-slate-400">
          Missing: {display.missing_components.join(', ')}
        </div>
      ) : null}
    </div>
  );
}

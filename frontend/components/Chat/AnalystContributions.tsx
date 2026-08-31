import type { TracePersona } from '@/lib/api/types';

interface AnalystContributionsProps {
  personas?: TracePersona[] | null;
  compact?: boolean;
}

function influenceLabel(value?: string): string {
  const labels: Record<string, string> = {
    included_as_prompt_constraint: 'Included in synthesis',
    reconciled_with_other_contributions: 'Reconciled with other contributions',
    rejected_from_synthesis: 'Rejected from synthesis',
  };
  return labels[value || ''] || 'Influence not recorded';
}

function percent(value?: number | null): string {
  if (typeof value !== 'number' || !Number.isFinite(value)) return 'Not measured';
  const normalized = value <= 1 ? value * 100 : value;
  return `${normalized.toFixed(1)}%`;
}

export function AnalystContributions({
  personas,
  compact = false,
}: AnalystContributionsProps) {
  if (!personas?.length) return null;

  return (
    <section className="space-y-3" aria-label="Governed analyst contributions">
      <div>
        <h3 className="text-sm font-semibold">{compact ? 'Analyst contributions' : 'Governed analyst contributions'}</h3>
        <p className="mt-1 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
          These are deterministic governed review findings, not separate provider-generated answers. The released combined answer remains outside this section.
        </p>
      </div>
      <div className={`grid grid-cols-1 gap-3 ${compact ? '' : 'md:grid-cols-2'}`}>
        {personas.map((persona, index) => {
          const finding = persona.finding
            || persona.draft?.text
            || persona.final_position
            || persona.initial_position
            || 'No governed finding was recorded.';
          const influence = persona.synthesis_influence;
          return (
            <article key={persona.persona_id || `${persona.persona_type}-${index}`} className="rounded-lg border border-slate-200 bg-white/70 p-3 dark:border-white/10 dark:bg-white/5">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h4 className="text-sm font-semibold">{persona.persona_name || persona.persona_type}</h4>
                  <div className="text-[10px] font-medium uppercase tracking-wide text-slate-500 dark:text-slate-400">
                    {persona.persona_type} analyst
                  </div>
                </div>
                <span className="rounded-full border px-2 py-0.5 text-[10px] font-medium">
                  {influenceLabel(influence?.disposition)}
                </span>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-slate-700 dark:text-slate-200">{finding}</p>
              <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] text-slate-500 dark:text-slate-400">
                <div>
                  <div className="font-medium text-slate-600 dark:text-slate-300">Finding measurement</div>
                  <div>{(persona.measurement_status || 'not_measured').replace(/_/g, ' ')}</div>
                </div>
                <div>
                  <div className="font-medium text-slate-600 dark:text-slate-300">Profile coverage</div>
                  <div>{percent(persona.profile_coverage)}</div>
                </div>
                <div>
                  <div className="font-medium text-slate-600 dark:text-slate-300">Evidence links</div>
                  <div>{persona.evidence_ids?.length || 0}</div>
                </div>
                <div>
                  <div className="font-medium text-slate-600 dark:text-slate-300">Synthesis weight</div>
                  <div>{percent(influence?.authority_weight)}</div>
                </div>
              </div>
              <p className="mt-2 text-[10px] text-slate-500 dark:text-slate-400">
                Deterministic review finding; not a separate provider answer.
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}

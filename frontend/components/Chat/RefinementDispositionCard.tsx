import type { TraceRefinementDisposition } from '@/lib/api/types';

interface RefinementDispositionCardProps {
  disposition?: TraceRefinementDisposition | null;
  compact?: boolean;
}

const STATUS_LABELS: Record<string, string> = {
  not_enabled: 'Not enabled',
  not_needed: 'Not needed',
  not_measured: 'Not measured',
  executed: 'Executed',
  blocked: 'Blocked',
  failed: 'Failed',
};

const REASON_EXPLANATIONS: Record<string, string> = {
  standard_mode_provider_budget:
    'Standard mode permits one provider attempt, so the 12-step rewrite workflow was not enabled.',
  measured_candidate_met_release_gate:
    'The measured candidate met the release gate without a rewrite.',
  convergence_did_not_request_refinement:
    'The governed convergence decision did not request a rewrite.',
  candidate_measurement_unavailable:
    'The inputs required to decide whether refinement was needed were not measured.',
  canonical_workflow_and_rewrite_completed:
    'The canonical 12-step workflow completed and one governed rewrite was performed.',
  refinement_step_blocked:
    'A required refinement step blocked the rewrite. Review the ordered step receipts.',
  refinement_step_failed:
    'A refinement step failed. The rewrite was not released.',
  provider_rewrite_failed:
    'The 12-step workflow completed, but the governed provider rewrite failed.',
  post_rewrite_validation_failed:
    'The rewrite completed but did not pass the post-rewrite validation gate.',
};

export function RefinementDispositionCard({
  disposition,
  compact = false,
}: RefinementDispositionCardProps) {
  const status = disposition?.status || 'not_recorded';
  const label = STATUS_LABELS[status] || 'Not recorded';
  const explanation = disposition
    ? REASON_EXPLANATIONS[disposition.reason]
      || `Recorded reason: ${disposition.reason.replace(/_/g, ' ')}.`
    : 'This historical run does not contain a refinement decision receipt.';

  return (
    <div className={`rounded-lg border border-slate-200 bg-white/70 dark:border-white/10 dark:bg-white/5 ${compact ? 'p-2' : 'p-3'}`}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs font-medium text-slate-600 dark:text-slate-300">Refinement decision</span>
        <span className="text-xs font-semibold">{label}</span>
      </div>
      <p className="mt-1 text-xs leading-relaxed text-slate-600 dark:text-slate-300">{explanation}</p>
      {disposition && (
        <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 font-mono text-[10px] text-slate-500 dark:text-slate-400">
          <span>{disposition.step_count}/12 steps accounted</span>
          <span>Rewrite: {disposition.rewrite_performed ? 'yes' : 'no'}</span>
          <span>Measurement: {disposition.measurement_status.replace(/_/g, ' ')}</span>
        </div>
      )}
    </div>
  );
}

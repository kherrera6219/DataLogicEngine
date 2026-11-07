import React, { useState } from 'react';
import { api } from '@/lib/api';
import type { TraceBundle } from '@/lib/api/types';

export function AnswerSources({ runId }: { runId: string }) {
  const [open, setOpen] = useState(false);
  const [bundle, setBundle] = useState<TraceBundle | null>(null);
  const [loading, setLoading] = useState(false);
  const [unavailable, setUnavailable] = useState(false);

  async function toggle() {
    const next = !open;
    setOpen(next);
    if (!next || bundle || loading) return;
    setLoading(true);
    setUnavailable(false);
    try {
      setBundle(await api.trace.getBundle(runId));
    } catch {
      setUnavailable(true);
    } finally {
      setLoading(false);
    }
  }

  const citations = bundle?.citations || [];
  return (
    <section className="text-xs" aria-label="Answer sources">
      <button type="button" onClick={() => void toggle()} aria-expanded={open} className="font-medium underline">Sources</button>
      {open && <div className="mt-2 space-y-2">
        {loading && <p>Loading recorded sources…</p>}
        {unavailable && <p role="status">Recorded sources are unavailable. Close and reopen to retry.</p>}
        {bundle && citations.length === 0 && <p>No resolved citations were recorded for this answer.</p>}
        {bundle && citations.map((citation, index) => {
          const evidence = bundle.evidence_sources?.find((item) => item.evidence_id === citation.evidence_id);
          const label = typeof citation.label === 'string' ? citation.label : 'Citation';
          const isChat = evidence?.source_type === 'chat_memory';
          return <div key={String(citation.citation_id || index)} className="rounded border p-2">
            <p className="font-medium">[{label}] {evidence?.title || 'Source details unavailable'}</p>
            <p>{isChat ? 'Prior conversation history; not independent evidence.' : evidence?.source_type || 'Source type unavailable.'}</p>
            {evidence?.snippet && <p className="mt-1 whitespace-pre-wrap">{evidence.snippet}</p>}
          </div>;
        })}
      </div>}
    </section>
  );
}

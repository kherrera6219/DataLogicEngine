import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { AnswerSources } from './AnswerSources';
import { api } from '@/lib/api';

vi.mock('@/lib/api', () => ({ api: { trace: { getBundle: vi.fn() } } }));

describe('AnswerSources', () => {
  it('identifies a cited earlier conversation as conversation history', async () => {
    vi.mocked(api.trace.getBundle).mockResolvedValueOnce({
      run_id: 'run-1', status: 'completed',
      citations: [{ citation_id: 'c1', label: 'S1', evidence_id: 'e1' }],
      evidence_sources: [{ evidence_id: 'e1', run_id: 'run-1', source_type: 'chat_memory', title: 'Previous question' }],
    } as Awaited<ReturnType<typeof api.trace.getBundle>>);
    render(<AnswerSources runId="run-1" />);
    fireEvent.click(screen.getByRole('button', { name: 'Sources' }));
    expect(await screen.findByText('Prior conversation history; not independent evidence.')).toBeInTheDocument();
    expect(screen.getByText('[S1] Previous question')).toBeInTheDocument();
  });

  it('shows an unavailable state when a trace cannot be read', async () => {
    vi.mocked(api.trace.getBundle).mockRejectedValueOnce(new Error('unavailable'));
    render(<AnswerSources runId="run-1" />);
    fireEvent.click(screen.getByRole('button', { name: 'Sources' }));
    expect(await screen.findByText(/Recorded sources are unavailable/)).toBeInTheDocument();
  });
});

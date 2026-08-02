import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import AlgorithmsPage from './page';
import { algorithms, request } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  request: vi.fn(),
  algorithms: {
    runs: vi.fn(),
    run: vi.fn(),
    plan: vi.fn(),
    execute: vi.fn(),
    cancel: vi.fn(),
    result: vi.fn(),
    trace: vi.fn(),
    artifacts: vi.fn(),
    effects: vi.fn(),
  },
  isKATerminalStatus: vi.fn((status: string) =>
    ['succeeded', 'failed', 'blocked', 'cancelled'].includes(status)),
}));

describe('AlgorithmsPage', () => {
  const mockedRequest = vi.mocked(request);
  const mockedAlgorithms = vi.mocked(algorithms);

  beforeEach(() => {
    window.history.replaceState({}, '', '/algorithms');
    mockedRequest.mockReset();
    mockedAlgorithms.runs.mockReset();
    mockedAlgorithms.run.mockReset();
    mockedAlgorithms.plan.mockReset();
    mockedAlgorithms.execute.mockReset();
    mockedAlgorithms.cancel.mockReset();
    mockedAlgorithms.result.mockReset();
    mockedAlgorithms.trace.mockReset();
    mockedAlgorithms.artifacts.mockReset();
    mockedAlgorithms.effects.mockReset();
    mockedAlgorithms.runs.mockResolvedValue({ success: true, runs: [] });
  });

  it('renders and searches KA card descriptions from purpose or description fields', async () => {
    mockedRequest.mockResolvedValue({
      algorithms: [
        {
          id: 'KA-001',
          name: 'Algorithm of Thought',
          category: 'Reasoning',
          purpose: 'Decompose query into ordered tasks and dependencies',
          risk_class: 'Low',
          classification: 'deterministic_heuristic',
          production_enabled: true,
          guarantee: 'Repeatable for identical versioned inputs.',
          limitations: 'This is a heuristic, not factual proof.',
          catalog_version: 'ka-catalog.v1',
        },
        {
          id: 'KA-018',
          name: 'Source Provenance',
          category: 'Trust',
          description: 'Track source origin, authority, and trust weight',
          risk_class: 'Low',
        },
      ],
    });

    render(<AlgorithmsPage />);

    expect(await screen.findByText('Algorithm of Thought')).toBeInTheDocument();
    expect(screen.getByText('Decompose query into ordered tasks and dependencies')).toBeInTheDocument();
    expect(screen.getByText('Track source origin, authority, and trust weight')).toBeInTheDocument();
    expect(screen.getByText('Production enabled')).toBeInTheDocument();
    expect(screen.getByText('deterministic heuristic')).toBeInTheDocument();
    expect(screen.getByText(/Repeatable for identical versioned inputs/)).toBeInTheDocument();
    expect(screen.getByText(/This is a heuristic, not factual proof/)).toBeInTheDocument();
    expect(screen.queryByText('No algorithm description is available.')).not.toBeInTheDocument();

    fireEvent.change(screen.getByLabelText('Search algorithms'), {
      target: { value: 'source origin' },
    });

    expect(screen.getByText('Source Provenance')).toBeInTheDocument();
    expect(screen.queryByText('Algorithm of Thought')).not.toBeInTheDocument();
  });

  it('reviews an exact server plan before queueing a high-risk KA run', async () => {
    const run = {
      schema_version: 'dle.ka-product-run.v1' as const,
      run_id: 'run-19j',
      request_id: 'request-19j',
      canonical_id: 'KA-004',
      manifest_version: '2026.07.25-cp19j.1',
      status: 'planned' as const,
      mode: 'production' as const,
      risk_tier: 'destructive' as const,
      confirmation_required: true,
      confirmed: false,
      cancellation_requested: false,
      result_size_bytes: null,
      error_code: null,
      error_message: null,
      created_at: '2026-07-25T00:00:00Z',
      updated_at: '2026-07-25T00:00:00Z',
      started_at: null,
      completed_at: null,
      expires_at: '2026-07-26T00:00:00Z',
      status_url: '/api/v1/ka/runs/run-19j',
      execute_url: '/api/v1/ka/runs/run-19j/execute',
      cancel_url: '/api/v1/ka/runs/run-19j/cancel',
      result_url: '/api/v1/ka/runs/run-19j/result',
      trace_url: '/api/v1/ka/runs/run-19j/trace',
      artifacts_url: '/api/v1/ka/runs/run-19j/artifacts',
      effects_url: '/api/v1/ka/runs/run-19j/effects',
    };
    mockedRequest.mockResolvedValue({
      algorithms: [{
        id: 'KA-004',
        name: 'Input Validation',
        category: 'Safety',
        purpose: 'Validate and normalize input',
        risk_class: 'Critical',
        production_enabled: true,
      }],
    });
    mockedAlgorithms.plan.mockResolvedValue({
      success: true,
      run,
      plan: {
        plan_id: 'plan-19j',
        manifest_version: run.manifest_version,
        valid: true,
        validation_errors: [],
        selected_ids: ['KA-004'],
        execution_order: [['KA-004']],
        selected_count: 1,
        dependency_count: 0,
        effect_proposal_count: 0,
        estimated_critical_path_ms: 1000,
        risk: {
          tier: 'destructive',
          risk_classes: ['critical'],
          effect_oriented_ids: [],
          effect_ports: [],
          confirmation_reasons: ['high_or_critical_risk'],
        },
        entries: {},
      },
      confirmation_token: 'confirm-19j',
    });
    mockedAlgorithms.execute.mockResolvedValue({
      success: true,
      run: { ...run, status: 'queued', confirmed: true },
    });

    render(<AlgorithmsPage />);

    expect(await screen.findByText('Input Validation')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Plan and run' }));
    fireEvent.change(screen.getByLabelText('Algorithm input (JSON object)'), {
      target: { value: '{"query":"validate this"}' },
    });
    fireEvent.click(screen.getByRole('button', { name: 'Review execution plan' }));

    expect(await screen.findByText('Reviewed execution plan')).toBeInTheDocument();
    expect(screen.getAllByText('KA-004').length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole('button', { name: 'Confirm and execute' }));
    fireEvent.click(await screen.findByRole('button', { name: 'Confirm exact plan' }));

    expect(mockedAlgorithms.plan).toHaveBeenCalledWith(
      expect.objectContaining({
        ka_id: 'KA-004',
        input: { query: 'validate this' },
        mode: 'production',
      }),
    );
    expect(mockedAlgorithms.execute).toHaveBeenCalledWith(
      'run-19j',
      'confirm-19j',
    );
  });

  it('opens any principal-owned history link and renders artifact/effect evidence', async () => {
    window.history.replaceState({}, '', '/algorithms?run=run-older-than-recent');
    mockedRequest.mockResolvedValue({
      algorithms: [{
        id: 'KA-071',
        name: 'Secure Acquisition',
        category: 'Knowledge',
        purpose: 'Qualify acquired knowledge',
        risk_class: 'Medium',
        production_enabled: true,
      }],
    });
    const run = {
      schema_version: 'dle.ka-product-run.v1' as const,
      run_id: 'run-older-than-recent',
      request_id: 'request-history',
      canonical_id: 'KA-071',
      manifest_version: '2026.07.25-cp19j.1',
      status: 'succeeded' as const,
      mode: 'production' as const,
      risk_tier: 'write' as const,
      confirmation_required: true,
      confirmed: true,
      cancellation_requested: false,
      result_size_bytes: 512,
      error_code: null,
      error_message: null,
      created_at: '2026-07-25T00:00:00Z',
      updated_at: '2026-07-25T00:00:01Z',
      started_at: '2026-07-25T00:00:00Z',
      completed_at: '2026-07-25T00:00:01Z',
      expires_at: '2026-07-26T00:00:00Z',
      status_url: '/api/v1/ka/runs/run-older-than-recent',
      execute_url: '/api/v1/ka/runs/run-older-than-recent/execute',
      cancel_url: '/api/v1/ka/runs/run-older-than-recent/cancel',
      result_url: '/api/v1/ka/runs/run-older-than-recent/result',
      trace_url: '/api/v1/ka/runs/run-older-than-recent/trace',
      artifacts_url: '/api/v1/ka/runs/run-older-than-recent/artifacts',
      effects_url: '/api/v1/ka/runs/run-older-than-recent/effects',
    };
    mockedAlgorithms.run.mockResolvedValue({ success: true, run });
    mockedAlgorithms.result.mockResolvedValue({
      success: true,
      result: { accepted: true },
    });
    mockedAlgorithms.trace.mockResolvedValue({
      success: true,
      trace: { status: 'succeeded' },
    });
    mockedAlgorithms.artifacts.mockResolvedValue({
      artifacts: [{ artifact_id: 'artifact-1', kind: 'evidence' }],
    });
    mockedAlgorithms.effects.mockResolvedValue({
      effects: [{ effect_id: 'effect-1', status: 'proposed' }],
    });

    render(<AlgorithmsPage />);

    expect(await screen.findByText('KA-071 · Secure Acquisition')).toBeInTheDocument();
    expect(mockedAlgorithms.run).toHaveBeenCalledWith('run-older-than-recent');
    expect(await screen.findByText('Artifacts (1)')).toBeInTheDocument();
    expect(screen.getByText('Effects (1)')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Artifacts (1)'));
    expect(screen.getByText(/artifact-1/)).toBeInTheDocument();
    fireEvent.click(screen.getByText('Effects (1)'));
    expect(screen.getByText(/effect-1/)).toBeInTheDocument();
  });
});

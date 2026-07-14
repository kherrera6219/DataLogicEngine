import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import AlgorithmsPage from './page';
import { request } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  request: vi.fn(),
}));

describe('AlgorithmsPage', () => {
  const mockedRequest = vi.mocked(request);

  beforeEach(() => {
    mockedRequest.mockReset();
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
});

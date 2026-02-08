import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { TraceVisualizer } from './TraceVisualizer';
import { TracePipeline } from './types';

describe('TraceVisualizer', () => {
  it('should show empty state before query runs', () => {
    render(<TraceVisualizer />);
    expect(screen.getByText('Interactive Trace Explorer')).toBeInTheDocument();
    expect(screen.getByText(/Run a query to populate the trace timeline/i)).toBeInTheDocument();
    expect(screen.queryByText('TruthGate Security')).not.toBeInTheDocument();
  });

  it('should render trace steps when trace data exists', () => {
    const trace: TracePipeline = {
      currentStepId: '2',
      totalDurationMs: 1200,
      estimatedTotalMs: 1500,
      overallProgress: 80,
      steps: [
        { id: '1', name: 'TruthGate Security', status: 'completed', durationMs: 100, percentage: 100, timestamp: '0.1s' },
        { id: '2', name: 'Coordinate Resolution', status: 'processing', durationMs: 300, percentage: 70, timestamp: 'current' },
      ],
    };

    render(<TraceVisualizer trace={trace} hasExecutedQuery />);
    expect(screen.getAllByText('TruthGate Security')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Coordinate Resolution')[0]).toBeInTheDocument();
    expect(screen.queryByText(/Run a query to populate the trace timeline/i)).not.toBeInTheDocument();
  });
});

import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
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

    const view = render(<TraceVisualizer trace={trace} hasExecutedQuery />);
    expect(screen.getByText('TruthGate Security')).toBeInTheDocument();
    expect(screen.getAllByText('Coordinate Resolution')[0]).toBeInTheDocument();
    expect(screen.queryByText(/Run a query to populate the trace timeline/i)).not.toBeInTheDocument();

    const treeTab = screen.getByRole('tab', { name: 'Tree view' });
    const timelineTab = screen.getByRole('tab', { name: 'Timeline view' });
    treeTab.focus();
    fireEvent.keyDown(treeTab, { key: 'ArrowRight' });
    expect(timelineTab).toHaveFocus();
    expect(timelineTab).toHaveAttribute('aria-selected', 'true');

    fireEvent.click(screen.getByRole('button', { name: /Coordinate Resolution/i }));
    expect(screen.getByText('Selected stage details')).toBeInTheDocument();
    expect(screen.getByText('current')).toBeInTheDocument();

    view.rerender(<TraceVisualizer trace={{ ...trace, overallProgress: 90 }} hasExecutedQuery />);
    expect(screen.getByRole('button', { name: /Coordinate Resolution/i })).toHaveAttribute('aria-expanded', 'true');
  });

  it('keeps long workflows in a scrollable list without truncating stages', () => {
    const steps = Array.from({ length: 26 }, (_, index) => ({
      id: `step-${index + 1}`,
      name: `Workflow stage ${index + 1}`,
      status: 'completed' as const,
      percentage: 100,
      timestamp: `${index + 1}s`,
    }));
    render(<TraceVisualizer trace={{ currentStepId: 'step-26', steps, totalDurationMs: 26, estimatedTotalMs: 26, overallProgress: 100 }} hasExecutedQuery />);

    expect(screen.getByText('Workflow stage 1')).toBeInTheDocument();
    expect(screen.getAllByText('Workflow stage 26')[0]).toBeInTheDocument();
    expect(screen.getByRole('list', { name: 'Trace stages' })).toHaveClass('overflow-y-auto');
  });
});

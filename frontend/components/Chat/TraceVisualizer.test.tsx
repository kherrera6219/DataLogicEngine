import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { TraceVisualizer } from './TraceVisualizer';

describe('TraceVisualizer', () => {
  it('should render trace steps', () => {
    render(<TraceVisualizer />);
    expect(screen.getByText('Interactive Trace Explorer')).toBeInTheDocument();
    // Use getAllByText as it might appear in both timeline and list views
    expect(screen.getAllByText('TruthGate Security')[0]).toBeInTheDocument();
    expect(screen.getAllByText('Coordinate Resolution')[0]).toBeInTheDocument();
  });
});

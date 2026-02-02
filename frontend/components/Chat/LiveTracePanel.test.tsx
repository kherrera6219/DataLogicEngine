import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { LiveTracePanel } from './LiveTracePanel';

// Mock UI components
vi.mock('@/components/ui/progress', () => ({
  Progress: ({ value }: { value: number }) => <div data-testid="progress" data-value={value} />
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}));

describe('LiveTracePanel', () => {
  it('should render correct header and active status', () => {
    render(<LiveTracePanel />);
    expect(screen.getByText('Live Trace')).toBeInTheDocument();
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();
  });

  it('should render active query and confidence', () => {
    render(<LiveTracePanel />);
    expect(screen.getByText('Active Query')).toBeInTheDocument();
    expect(screen.getByText('Target:')).toBeInTheDocument();
  });

  it('should render step progress', () => {
    render(<LiveTracePanel />);
    const progress = screen.getByTestId('progress');
    expect(progress).toBeInTheDocument();
  });
});

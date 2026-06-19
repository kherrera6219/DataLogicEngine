import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RouteErrorFallback } from './route-error-fallback';

// Mock the telemetry module
vi.mock('@/lib/telemetry/client-errors', () => ({
  reportClientError: vi.fn(),
}));

// Mock lucide-react icons
vi.mock('lucide-react', () => ({
  AlertTriangle: () => <span data-testid="alert-icon">AlertTriangle</span>,
  RefreshCw: () => <span data-testid="refresh-icon">RefreshCw</span>,
}));

// Mock Button component
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: any) => <button {...props}>{children}</button>,
}));

import { reportClientError } from '@/lib/telemetry/client-errors';

describe('RouteErrorFallback', () => {
  const mockError = new Error('Test error message');
  const mockReset = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render error fallback UI', () => {
    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName="TestModule" />
    );

    expect(screen.getByText('Module Error')).toBeInTheDocument();
    expect(screen.getByText(/Component: TestModule/)).toBeInTheDocument();
  });

  it('should display error message', () => {
    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName="TestModule" />
    );

    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('should display alert icon', () => {
    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName="TestModule" />
    );

    expect(screen.getByTestId('alert-icon')).toBeInTheDocument();
  });

  it('should have a retry button with refresh icon', () => {
    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName="TestModule" />
    );

    const retryButton = screen.getByRole('button', { name: /Retry Module/i });
    expect(retryButton).toBeInTheDocument();
    expect(screen.getByTestId('refresh-icon')).toBeInTheDocument();
  });

  it('should call reset function when retry button clicked', () => {
    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName="TestModule" />
    );

    const retryButton = screen.getByRole('button', { name: /Retry Module/i });
    fireEvent.click(retryButton);

    expect(mockReset).toHaveBeenCalledTimes(1);
  });

  it('should report error on mount', () => {
    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName="TestModule" />
    );

    expect(reportClientError).toHaveBeenCalledWith(mockError, {
      module: 'TestModule',
      action: 'route-error',
    });
  });

  it('should report error when error changes', () => {
    const { rerender } = render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName="TestModule" />
    );

    const newError = new Error('New error message');
    rerender(
      <RouteErrorFallback error={newError} reset={mockReset} moduleName="TestModule" />
    );

    expect(reportClientError).toHaveBeenCalledWith(newError, {
      module: 'TestModule',
      action: 'route-error',
    });
  });

  it('should display recovery message', () => {
    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName="TestModule" />
    );

    expect(screen.getByText(/The module failed to render/)).toBeInTheDocument();
    expect(screen.getByText(/Retry to recover this route segment/)).toBeInTheDocument();
  });

  it('should handle error with digest property', () => {
    const errorWithDigest = new Error('Error with digest');
    (errorWithDigest as any).digest = 'abc123';

    render(
      <RouteErrorFallback
        error={errorWithDigest}
        reset={mockReset}
        moduleName="TestModule"
      />
    );

    expect(screen.getByText('Error with digest')).toBeInTheDocument();
  });
});

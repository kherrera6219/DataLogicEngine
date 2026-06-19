import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RouteErrorFallback } from './route-error-fallback';

// Mock telemetry
vi.mock('@/lib/telemetry/client-errors', () => ({
  reportClientError: vi.fn(),
}));

// Mock UI components
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, ...props }: { children: React.ReactNode; onClick?: () => void; [key: string]: any }) => (
    <button data-testid="reset-button" onClick={onClick} {...props}>
      {children}
    </button>
  ),
}));

vi.mock('lucide-react', () => ({
  RefreshCw: () => <span data-testid="refresh-icon">↻</span>,
  AlertTriangle: () => <span data-testid="alert-icon">⚠</span>,
}));

import { reportClientError } from '@/lib/telemetry/client-errors';

describe('RouteErrorFallback', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const mockError = new Error('Test error message');
  mockError.digest = 'test-digest-123';

  const mockReset = vi.fn();
  const moduleName = 'TestModule';

  it('should render error fallback UI', () => {
    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName={moduleName} />
    );

    expect(screen.getByText('Module Error')).toBeInTheDocument();
    expect(screen.getByText(`Component: ${moduleName}`)).toBeInTheDocument();
  });

  it('should display error message', () => {
    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName={moduleName} />
    );

    expect(screen.getByText('Test error message')).toBeInTheDocument();
  });

  it('should display alert icon', () => {
    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName={moduleName} />
    );

    expect(screen.getByTestId('alert-icon')).toBeInTheDocument();
  });

  it('should display reset button with refresh icon', () => {
    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName={moduleName} />
    );

    expect(screen.getByTestId('reset-button')).toBeInTheDocument();
    expect(screen.getByTestId('refresh-icon')).toBeInTheDocument();
    expect(screen.getByText('Retry Module')).toBeInTheDocument();
  });

  it('should call reset function when button is clicked', () => {
    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName={moduleName} />
    );

    const resetButton = screen.getByTestId('reset-button');
    fireEvent.click(resetButton);

    expect(mockReset).toHaveBeenCalledTimes(1);
  });

  it('should report error on mount', () => {
    const mockedReportError = vi.mocked(reportClientError);

    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName={moduleName} />
    );

    expect(mockedReportError).toHaveBeenCalledWith(mockError, {
      module: moduleName,
      action: 'route-error',
    });
  });

  it('should show helpful message to user', () => {
    render(
      <RouteErrorFallback error={mockError} reset={mockReset} moduleName={moduleName} />
    );

    expect(screen.getByText(/The module failed to render/i)).toBeInTheDocument();
    expect(screen.getByText(/Retry to recover/i)).toBeInTheDocument();
  });

  it('should render with different module names', () => {
    const modules = ['Dashboard', 'Settings', 'ChatPanel'];

    modules.forEach((module) => {
      const { unmount } = render(
        <RouteErrorFallback error={mockError} reset={mockReset} moduleName={module} />
      );

      expect(screen.getByText(`Component: ${module}`)).toBeInTheDocument();
      unmount();
    });
  });

  it('should handle errors with and without digest', () => {
    const errorWithDigest = new Error('Error with digest');
    errorWithDigest.digest = 'digest-123';

    const errorWithoutDigest = new Error('Error without digest');

    const { unmount } = render(
      <RouteErrorFallback error={errorWithDigest} reset={mockReset} moduleName={moduleName} />
    );

    expect(screen.getByText('Error with digest')).toBeInTheDocument();

    unmount();

    render(
      <RouteErrorFallback error={errorWithoutDigest} reset={mockReset} moduleName={moduleName} />
    );

    expect(screen.getByText('Error without digest')).toBeInTheDocument();
  });
});

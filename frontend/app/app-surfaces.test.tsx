import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import AppLoading from './loading';
import ChatLoading from './chat/loading';
import NotFound from './not-found';
import GlobalError from './global-error';
import AdminError from './admin/error';
import AnalyticsError from './analytics/error';
import ChatError from './chat/error';
import DashboardError from './dashboard/error';
import GraphError from './graph/error';
import McpError from './mcp/error';
import ProjectsError from './projects/error';
import RunsError from './runs/error';
import SettingsError from './settings/error';
import SimulationsError from './simulations/error';
import TruthEngineError from './truth-engine/error';

const mockPush = vi.fn();
const mockReportClientError = vi.fn();
const mockRemoveLocalStorageItem = vi.fn();

vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button type="button" {...props}>
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/route-error-fallback', () => ({
  RouteErrorFallback: ({
    error,
    moduleName,
  }: {
    error: Error;
    moduleName: string;
  }) => (
    <div data-testid={`route-error-${moduleName.toLowerCase()}`}>
      {moduleName}:{error.message}
    </div>
  ),
}));

vi.mock('@/lib/telemetry/client-errors', () => ({
  reportClientError: (...args: unknown[]) => mockReportClientError(...args),
}));

vi.mock('@/lib/state/storage', () => ({
  removeLocalStorageItem: (...args: unknown[]) => mockRemoveLocalStorageItem(...args),
}));

describe('frontend app surfaces', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it('renders the generic loading states', () => {
    render(
      <>
        <AppLoading />
        <ChatLoading />
      </>,
    );

    expect(screen.getByText('Loading workspace...')).toBeInTheDocument();
    expect(screen.getByText('Bootstrapping chat session...')).toBeInTheDocument();
  });

  it('renders the not-found page and returns to the dashboard', () => {
    render(<NotFound />);

    expect(screen.getByText('404')).toBeInTheDocument();
    expect(screen.getByText('Page Not Found')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /return to dashboard/i }));
    expect(mockPush).toHaveBeenCalledWith('/dashboard');
  });

  it('wires module-specific route error boundaries', () => {
    const error = new Error('route failed');
    const reset = vi.fn();

    render(
      <>
        <AdminError error={error} reset={reset} />
        <AnalyticsError error={error} reset={reset} />
        <ChatError error={error} reset={reset} />
        <DashboardError error={error} reset={reset} />
        <GraphError error={error} reset={reset} />
        <McpError error={error} reset={reset} />
        <ProjectsError error={error} reset={reset} />
        <RunsError error={error} reset={reset} />
        <SettingsError error={error} reset={reset} />
        <SimulationsError error={error} reset={reset} />
        <TruthEngineError error={error} reset={reset} />
      </>,
    );

    expect(screen.getByTestId('route-error-admin')).toHaveTextContent('Admin:route failed');
    expect(screen.getByTestId('route-error-analytics')).toHaveTextContent('Analytics:route failed');
    expect(screen.getByTestId('route-error-chat')).toHaveTextContent('Chat:route failed');
    expect(screen.getByTestId('route-error-dashboard')).toHaveTextContent('Dashboard:route failed');
    expect(screen.getByTestId('route-error-graph')).toHaveTextContent('Graph:route failed');
    expect(screen.getByTestId('route-error-mcp')).toHaveTextContent('MCP:route failed');
    expect(screen.getByTestId('route-error-projects')).toHaveTextContent('Projects:route failed');
    expect(screen.getByTestId('route-error-runs')).toHaveTextContent('Runs:route failed');
    expect(screen.getByTestId('route-error-settings')).toHaveTextContent('Settings:route failed');
    expect(screen.getByTestId('route-error-simulations')).toHaveTextContent('Simulations:route failed');
    expect(screen.getByTestId('route-error-truth engine')).toHaveTextContent('Truth Engine:route failed');
  });

  it('reports and recovers from global errors', () => {
    vi.useFakeTimers();
    const reset = vi.fn();
    const error = Object.assign(new Error('fatal failure'), { digest: 'digest-1' });

    const originalLocation = window.location;
    delete (window as Partial<Window>).location;
    (window as Window & { location: { href: string } }).location = { href: 'http://localhost/' };

    render(<GlobalError error={error} reset={reset} />);

    expect(mockReportClientError).toHaveBeenCalledWith(
      error,
      expect.objectContaining({
        module: 'global-error',
        action: 'render',
      }),
    );
    expect(screen.getByText('System Error')).toBeInTheDocument();
    expect(screen.getByText('ID: digest-1')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /reload application/i }));

    expect(mockRemoveLocalStorageItem).toHaveBeenCalledWith('user-session');
    expect(reset).toHaveBeenCalled();

    vi.advanceTimersByTime(500);
    expect(window.location.href).toBe('/dashboard');

    fireEvent.click(screen.getByRole('button', { name: /return home/i }));
    expect(window.location.href).toBe('/');

    window.location = originalLocation;
  });

  it('shows the unknown error fallback when the message is empty', () => {
    const reset = vi.fn();
    const error = Object.assign(new Error(''), { digest: undefined });

    render(<GlobalError error={error} reset={reset} />);

    expect(screen.getByText('Unknown Error')).toBeInTheDocument();
  });
});

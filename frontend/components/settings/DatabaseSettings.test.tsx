import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DatabaseSettings from './DatabaseSettings';
import { request } from '@/lib/api';

const toastMock = vi.fn();

vi.mock('@/lib/api', () => ({
  request: vi.fn(),
}));

vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: toastMock }),
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardDescription: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TabsList: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  TabsTrigger: ({ children, onClick }: { children: React.ReactNode; onClick?: () => void }) => (
    <button onClick={onClick}>{children}</button>
  ),
  TabsContent: ({ children, value }: { children: React.ReactNode; value: string }) => (
    <div data-testid={`tab-${value}`}>{children}</div>
  ),
}));

describe('DatabaseSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    toastMock.mockReset();
  });

  it('should render loading state initially', () => {
    vi.mocked(request).mockReturnValue(new Promise(() => {}));
    render(<DatabaseSettings />);
  });

  it('should render active services', async () => {
    vi.mocked(request).mockResolvedValue({
      mode: 'local',
      services: {
        postgres: { healthy: true, is_cloud: false },
        redis: { healthy: false, is_cloud: false },
        neo4j: { healthy: true, is_cloud: false },
        vector: { healthy: true, is_cloud: false },
        object: { healthy: true, is_cloud: false },
      },
    });

    render(<DatabaseSettings />);

    await waitFor(() => {
      expect(screen.getByText('Database Connections')).toBeInTheDocument();
      expect(screen.getByText('PostgreSQL')).toBeInTheDocument();
      expect(screen.getByText('Redis')).toBeInTheDocument();
      expect(screen.getAllByText('Online').length).toBeGreaterThan(0);
      expect(screen.getAllByText('Offline').length).toBeGreaterThan(0);
    });
  });

  it('should handle start all databases', async () => {
    vi.mocked(request).mockResolvedValue({
      mode: 'local',
      services: {
        postgres: { healthy: true, is_cloud: false },
        redis: { healthy: false, is_cloud: false },
        neo4j: { healthy: true, is_cloud: false },
        vector: { healthy: true, is_cloud: false },
        object: { healthy: true, is_cloud: false },
      },
    });

    render(<DatabaseSettings />);
    await waitFor(() => screen.getByText('Start All'));

    fireEvent.click(screen.getByText('Start All'));
    expect(request).toHaveBeenCalledWith('/storage/databases/start', { method: 'POST' });
  });

  it('should persist auto-start toggle', async () => {
    vi.mocked(request).mockResolvedValue({
      mode: 'local',
      services: {
        postgres: { healthy: true, is_cloud: false },
        redis: { healthy: false, is_cloud: false },
        neo4j: { healthy: true, is_cloud: false },
        vector: { healthy: true, is_cloud: false },
        object: { healthy: true, is_cloud: false },
      },
    });

    render(<DatabaseSettings />);
    await waitFor(() => screen.getByRole('switch'));

    fireEvent.click(screen.getByRole('switch'));
    expect(request).toHaveBeenCalledWith('/storage/databases/autostart', expect.objectContaining({ method: 'POST' }));
  });
});

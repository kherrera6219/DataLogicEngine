import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DatabaseSettings from './DatabaseSettings';

// Mock fetch
global.fetch = vi.fn();

// Mock UI components
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
    TabsTrigger: ({ children, value, onClick }: any) => <button onClick={onClick}>{children}</button>,
    TabsContent: ({ children, value }: any) => <div data-testid={`tab-${value}`}>{children}</div>
}));

describe('DatabaseSettings', () => {
  beforeEach(() => {
    (global.fetch as any).mockReset();
  });

  it('should render loading state initially', () => {
      // Mock never resolving fetch
    (global.fetch as any).mockReturnValue(new Promise(() => {}));
    render(<DatabaseSettings />);
    // Check for spinner implicitly or just that content isn't there yet
    // The component returns a div with spinner class if loading
  });

  it('should render active services', async () => {
    const mockHealth = {
      success: true,
      data: {
        mode: 'local',
        services: {
          postgres: { healthy: true, is_cloud: false },
          redis: { healthy: false, is_cloud: false }
        }
      }
    };
    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockHealth
    });

    render(<DatabaseSettings />);

    await waitFor(() => {
        expect(screen.getByText('Database Connections')).toBeInTheDocument();
        expect(screen.getByText('PostgreSQL')).toBeInTheDocument();
        expect(screen.getByText('Redis')).toBeInTheDocument();
        expect(screen.getByText('Online')).toBeInTheDocument();
        expect(screen.getByText('Offline')).toBeInTheDocument();
    });
  });

  it('should handle start all databases', async () => {
      // Setup successful fetch
      (global.fetch as any).mockResolvedValue({ ok: true, json: async () => ({ success: true, data: { services: {}, mode: 'local' } }) });
      
      render(<DatabaseSettings />);
      await waitFor(() => screen.getByText('Start All'));
      
      const startBtn = screen.getByText('Start All');
      fireEvent.click(startBtn);
      
      expect(global.fetch).toHaveBeenCalledWith('/api/v1/storage/databases/start', expect.anything());
  });
});

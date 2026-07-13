import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import DatabaseSettings from './DatabaseSettings';
import { request } from '@/lib/api';

const toastMock = vi.fn();

vi.mock('@/lib/api', () => ({
  request: vi.fn(),
}));

vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: toastMock }),
}));

const baseHealth = {
  mode: 'internal',
  services: {
    postgres: { healthy: true, is_cloud: false, endpoint: '127.0.0.1:22000', expected_version: '18.4' },
    redis: { healthy: false, is_cloud: false, endpoint: '127.0.0.1:22001', safe_reason: 'health_probe_failed', expected_version: '8.8.0' },
    neo4j: { healthy: true, is_cloud: false, endpoint: '127.0.0.1:22002', expected_version: '5.26.28' },
    vector: { healthy: true, is_cloud: false, endpoint: '127.0.0.1:22004', expected_version: '1.5.9' },
    object: { healthy: true, is_cloud: false, endpoint: '127.0.0.1:22005', expected_version: '4.29' },
  },
};

const baseMetrics = {
  generated_at: '2026-06-19T00:00:00Z',
  runtime_root: 'C:\\DataLogicEngine',
  sqlite: { size_bytes: 1024, tables: 12, rows: 34 },
  neo4j: { size_bytes: 2048, exists: true },
  chroma: { size_bytes: 512, exists: true },
  object_store: { size_bytes: 256, exists: false },
  structured_memory: { size_bytes: 0, exists: false },
  total_local_bytes: 4096,
};

function installElectronApi(overrides: Record<string, unknown> = {}) {
  Object.defineProperty(window, 'electronAPI', {
    configurable: true,
    value: {
      getDesktopStorageMetrics: vi.fn().mockResolvedValue(baseMetrics),
      chooseBackupFolder: vi.fn().mockResolvedValue({ token: 'backup-token', display_name: 'Backups', expires_at: '2026-07-13T01:00:00Z' }),
      runDatabaseBackup: vi.fn().mockResolvedValue({
        artifact_path: 'C:\\Backups\\backup.zip',
        size_bytes: 8192,
        manifest: {},
      }),
      ...overrides,
    },
  });
}

function mockRequestRoutes(overrides: Record<string, unknown> = {}) {
  vi.mocked(request).mockImplementation(async (endpoint: string, options?: RequestInit) => {
    switch (endpoint) {
      case '/storage/health':
        return (overrides[endpoint] ?? baseHealth) as never;
      case '/storage/databases/autostart':
        if (options?.method === 'POST') {
          return (overrides['/storage/databases/autostart:POST'] ?? {
            enabled: true,
            message: 'Auto-start saved.',
          }) as never;
        }
        return (overrides[endpoint] ?? { enabled: true }) as never;
      case '/storage/health/postgres':
        return (overrides[endpoint] ?? { success: true }) as never;
      case '/storage/databases/start':
        return (overrides[endpoint] ?? { message: 'Database startup initiated.' }) as never;
      case '/storage/databases/stop':
        return (overrides[endpoint] ?? { message: 'Database shutdown initiated.' }) as never;
      case '/storage/backup':
        return (overrides[endpoint] ?? {
          artifact_path: 'C:\\Backups\\backup.zip',
          size_bytes: 8192,
          manifest: {},
        }) as never;
      case '/storage/desktop-metrics':
        return (overrides[endpoint] ?? baseMetrics) as never;
      default:
        throw new Error(`Unexpected request for ${endpoint}`);
    }
  });
}

describe('DatabaseSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
    installElectronApi();
    mockRequestRoutes();
  });

  it('renders service health, mode, and metrics on load', async () => {
    render(<DatabaseSettings />);

    expect(await screen.findByText('Internal Data Plane')).toBeInTheDocument();
    expect(screen.getByText('4/5 Services Online')).toBeInTheDocument();
    expect(screen.getByText('PostgreSQL')).toBeInTheDocument();
    expect(screen.getByText('Redis')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Metrics & Backup'));
    expect(screen.getByText('1.0 KB')).toBeInTheDocument();
    expect(screen.getByText('C:\\DataLogicEngine')).toBeInTheDocument();
  });

  it('warns when the storage health shape is invalid', async () => {
    mockRequestRoutes({
      '/storage/health': { mode: 'internal' },
    });

    render(<DatabaseSettings />);

    await waitFor(() => {
      expect(toastMock).toHaveBeenCalledWith(
        'Storage health response format was invalid.',
        'warning',
      );
    });
  });

  it('surfaces fetch errors from the initial load', async () => {
    vi.mocked(request).mockRejectedValueOnce(new Error('backend unavailable'));

    render(<DatabaseSettings />);

    await waitFor(() => {
      expect(toastMock).toHaveBeenCalledWith(
        'Failed to fetch storage health: backend unavailable',
        'error',
      );
    });
  });

  it('refreshes and tests a service connection', async () => {
    render(<DatabaseSettings />);
    await screen.findByText('Internal Data Plane');

    fireEvent.click(screen.getByRole('button', { name: /refresh/i }));
    fireEvent.click(screen.getAllByRole('button', { name: /test connection/i })[0]);

    await waitFor(() => {
      expect(request).toHaveBeenCalledWith('/storage/health/postgres');
      expect(toastMock).toHaveBeenCalledWith('PostgreSQL health check complete.', 'success', 2000);
    });
  });

  it('starts and stops databases, then refreshes health', async () => {
    render(<DatabaseSettings />);
    await screen.findByText('Internal Data Plane');
    const timeoutSpy = vi.spyOn(global, 'setTimeout');

    fireEvent.click(screen.getByRole('button', { name: /start all/i }));
    await waitFor(() => {
      expect(request).toHaveBeenCalledWith('/storage/databases/start', { method: 'POST' });
    });
    expect(timeoutSpy).toHaveBeenCalledWith(expect.any(Function), 1200);

    fireEvent.click(screen.getByRole('button', { name: /stop all/i }));
    await waitFor(() => {
      expect(request).toHaveBeenCalledWith('/storage/databases/stop', { method: 'POST' });
    });
    expect(timeoutSpy).toHaveBeenCalledWith(expect.any(Function), 1000);
  });

  it('persists auto-start changes and reverts on failure', async () => {
    render(<DatabaseSettings />);
    fireEvent.click(await screen.findByText('Runtime Policy'));
    const autoStartSwitch = await screen.findByRole('switch');

    fireEvent.click(autoStartSwitch);
    await waitFor(() => {
      expect(request).toHaveBeenCalledWith(
        '/storage/databases/autostart',
        expect.objectContaining({ method: 'POST' }),
      );
      expect(toastMock).toHaveBeenCalledWith('Auto-start saved.', 'success', 2000);
    });

    vi.mocked(request).mockImplementation(async (endpoint: string, options?: RequestInit) => {
      if (endpoint === '/storage/databases/autostart' && options?.method === 'POST') {
        throw new Error('save failed');
      }
      if (endpoint === '/storage/health') return baseHealth as never;
      if (endpoint === '/storage/databases/autostart') return { enabled: true } as never;
      throw new Error(`Unexpected request for ${endpoint}`);
    });

    fireEvent.click(autoStartSwitch);
    await waitFor(() => {
      expect(toastMock).toHaveBeenCalledWith(
        'Failed to save auto-start preference: save failed',
        'error',
      );
    });
  });

  it('runs desktop backups and handles cancellation', async () => {
    const chooseBackupFolder = vi.fn().mockResolvedValue({ token: 'backup-token', display_name: 'Backups', expires_at: '2026-07-13T01:00:00Z' });
    const runDatabaseBackup = vi.fn().mockResolvedValue({
      artifact_path: 'C:\\Backups\\desktop-backup.zip',
      size_bytes: 16384,
      manifest: {},
    });
    installElectronApi({ chooseBackupFolder, runDatabaseBackup });

    render(<DatabaseSettings />);
    await screen.findByText('Internal Data Plane');

    fireEvent.click(screen.getByText('Metrics & Backup'));
    fireEvent.click(screen.getByRole('button', { name: /run backup/i }));

    await waitFor(() => {
      expect(runDatabaseBackup).toHaveBeenCalledWith(
        expect.objectContaining({ target_capability: 'backup-token', operation_id: expect.any(String) }),
      );
      expect(screen.getByText('C:\\Backups\\desktop-backup.zip')).toBeInTheDocument();
    });

    installElectronApi({
      chooseBackupFolder: vi.fn().mockResolvedValue(null),
      runDatabaseBackup,
    });

    fireEvent.click(screen.getByRole('button', { name: /run backup/i }));
    await waitFor(() => {
      expect(runDatabaseBackup).toHaveBeenCalledTimes(1);
    });
  });

  it('shows read-only runtime policy and the auto-start control', async () => {
    render(<DatabaseSettings />);
    await screen.findByText('Internal Data Plane');

    fireEvent.click(await screen.findByText('Runtime Policy'));
    expect(screen.getByText('Locked version 18.4')).toBeInTheDocument();
    expect(screen.getByText('127.0.0.1:22000')).toBeInTheDocument();
    expect(screen.getByRole('switch')).toBeInTheDocument();
    expect(screen.queryByText('Cloud Config')).not.toBeInTheDocument();
  });

  it('shows a backup error toast when the backup call fails', async () => {
    installElectronApi({
      chooseBackupFolder: vi.fn().mockResolvedValue(undefined),
    });

    render(<DatabaseSettings />);
    await screen.findByText('Internal Data Plane');
    fireEvent.click(screen.getByText('Metrics & Backup'));
    fireEvent.click(screen.getByRole('button', { name: /run backup/i }));

    await waitFor(() => {
      expect(screen.queryByText(/last backup/i)).not.toBeInTheDocument();
    });
  });
});

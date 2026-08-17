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
    fireEvent.change(screen.getByLabelText('Recovery passphrase'), {
      target: { value: 'owner-recovery-secret' },
    });
    fireEvent.change(screen.getByLabelText('Confirm recovery passphrase'), {
      target: { value: 'owner-recovery-secret' },
    });
    fireEvent.click(screen.getByRole('button', { name: /run backup/i }));

    await waitFor(() => {
      expect(runDatabaseBackup).toHaveBeenCalledWith(
        expect.objectContaining({
          target_capability: 'backup-token',
          operation_id: expect.any(String),
          recovery_secret: 'owner-recovery-secret',
        }),
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

  it('renders all-healthy service details and policy fallbacks', async () => {
    const services = {
      postgres: { healthy: true, is_cloud: false, url: 'postgres://local', provider: 'bundled', version: '18.4' },
      redis: { healthy: true, is_cloud: false },
      neo4j: { healthy: true, is_cloud: false },
      vector: { healthy: true, is_cloud: false },
      object: { healthy: true, is_cloud: false },
    };
    mockRequestRoutes({ '/storage/health': { mode: '', services } });

    render(<DatabaseSettings />);
    expect(await screen.findByText('5/5 Services Online')).toBeInTheDocument();
    expect(screen.getByText('Provider: bundled')).toBeInTheDocument();
    expect(screen.getByText('Version: 18.4')).toBeInTheDocument();
    fireEvent.click(screen.getByText('Runtime Policy'));
    expect(screen.getAllByText('Endpoint unavailable')).toHaveLength(4);
    expect(screen.getAllByText('Version pending')).toHaveLength(5);
  });

  it('uses HTTP metrics fallback and formats bytes through gigabytes', async () => {
    const metrics = {
      ...baseMetrics,
      sqlite: { size_bytes: 512, tables: 0, rows: 0 },
      neo4j: { size_bytes: 2 * 1024 * 1024, exists: false },
      chroma: { size_bytes: 2 * 1024 * 1024 * 1024, exists: true },
      object_store: {},
      total_local_bytes: 0,
    };
    installElectronApi({ getDesktopStorageMetrics: undefined });
    mockRequestRoutes({ '/storage/desktop-metrics': metrics });

    render(<DatabaseSettings />);
    await screen.findByText('Internal Data Plane');
    fireEvent.click(screen.getByText('Metrics & Backup'));
    expect(screen.getByText('512 B')).toBeInTheDocument();
    expect(screen.getByText('2.0 MB')).toBeInTheDocument();
    expect(screen.getByText('2.0 GB')).toBeInTheDocument();
    expect(screen.getAllByText('0 B').length).toBeGreaterThan(0);
    expect(screen.getByText('Not created')).toBeInTheDocument();
  });

  it('reports connection and database lifecycle failures', async () => {
    render(<DatabaseSettings />);
    await screen.findByText('Internal Data Plane');
    vi.mocked(request).mockImplementation(async (endpoint: string) => {
      if (endpoint === '/storage/health') return baseHealth as never;
      if (endpoint === '/storage/databases/autostart') return { enabled: true } as never;
      if (endpoint === '/storage/health/postgres') throw 'probe denied';
      if (endpoint === '/storage/databases/start') throw new Error('start denied');
      if (endpoint === '/storage/databases/stop') throw 'stop denied';
      if (endpoint === '/storage/desktop-metrics') return baseMetrics as never;
      throw new Error(`Unexpected request for ${endpoint}`);
    });

    fireEvent.click(screen.getAllByRole('button', { name: /test connection/i })[0]);
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith(
      'Failed to test PostgreSQL: probe denied',
      'error',
    ));
    fireEvent.click(screen.getByRole('button', { name: /start all/i }));
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith('Failed to start databases: start denied', 'error'));
    fireEvent.click(screen.getByRole('button', { name: /stop all/i }));
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith('Failed to stop databases: stop denied', 'error'));
  });

  it('uses lifecycle and auto-start default success messages', async () => {
    mockRequestRoutes({
      '/storage/databases/start': {},
      '/storage/databases/stop': {},
      '/storage/databases/autostart:POST': {},
    });
    render(<DatabaseSettings />);
    await screen.findByText('Internal Data Plane');
    fireEvent.click(screen.getByRole('button', { name: /start all/i }));
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith('Database startup initiated.', 'success'));
    fireEvent.click(screen.getByRole('button', { name: /stop all/i }));
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith('Database shutdown initiated.', 'success'));
    fireEvent.click(screen.getByText('Runtime Policy'));
    fireEvent.click(await screen.findByRole('switch'));
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith('Auto-start preference saved.', 'success', 2000));
  });

  it('validates backup secrets and reports unavailable desktop backup support', async () => {
    installElectronApi({ chooseBackupFolder: undefined, runDatabaseBackup: undefined });
    render(<DatabaseSettings />);
    await screen.findByText('Internal Data Plane');
    fireEvent.click(screen.getByText('Metrics & Backup'));
    const runBackup = screen.getByRole('button', { name: /run backup/i });
    fireEvent.click(runBackup);
    expect(toastMock).toHaveBeenCalledWith('Use a recovery passphrase with at least 12 characters.', 'error');

    fireEvent.change(screen.getByLabelText('Recovery passphrase'), { target: { value: 'long-secret-123' } });
    fireEvent.change(screen.getByLabelText('Confirm recovery passphrase'), { target: { value: 'different-1234' } });
    fireEvent.click(runBackup);
    expect(toastMock).toHaveBeenCalledWith('Recovery passphrases do not match.', 'error');

    fireEvent.change(screen.getByLabelText('Confirm recovery passphrase'), { target: { value: 'long-secret-123' } });
    fireEvent.click(runBackup);
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith(
      'Backup failed: Database backup is available only in the desktop application.',
      'error',
    ));
  });

  it('requests cancellation for a running backup', async () => {
    type BackupResult = { artifact_path: string; size_bytes: number; manifest: Record<string, unknown> };
    let finishBackup: ((value: BackupResult) => void) | undefined;
    const runDatabaseBackup = vi.fn(() => new Promise<BackupResult>((resolve) => { finishBackup = resolve; }));
    const cancelDesktopOperation = vi.fn().mockResolvedValue({ cancelled: true });
    installElectronApi({ runDatabaseBackup, cancelDesktopOperation });

    render(<DatabaseSettings />);
    await screen.findByText('Internal Data Plane');
    fireEvent.click(screen.getByText('Metrics & Backup'));
    fireEvent.change(screen.getByLabelText('Recovery passphrase'), { target: { value: 'owner-secret-123' } });
    fireEvent.change(screen.getByLabelText('Confirm recovery passphrase'), { target: { value: 'owner-secret-123' } });
    fireEvent.click(screen.getByRole('button', { name: /run backup/i }));
    fireEvent.click(await screen.findByRole('button', { name: /cancel database backup/i }));
    await waitFor(() => expect(cancelDesktopOperation).toHaveBeenCalledWith(expect.any(String)));
    expect(toastMock).toHaveBeenCalledWith('Backup cancellation requested.', 'success', 3000);

    finishBackup?.({ artifact_path: 'C:\\Backups\\late.zip', size_bytes: 1, manifest: {} });
    await waitFor(() => expect(screen.getByText('C:\\Backups\\late.zip')).toBeInTheDocument());
  });
});

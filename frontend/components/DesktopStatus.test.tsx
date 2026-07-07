
import React from 'react';
import { render, screen, act, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import DesktopStatus from './DesktopStatus';

type ElectronLogHandler = (log: string) => void;

const idleUpdateState = {
  enabled: false,
  status: 'idle' as const,
  lastCheckAt: null,
  currentVersion: '0.0.0',
  availableVersion: null,
  message: '',
};

describe('DesktopStatus', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    // Default mock implementation
    window.electronAPI = {
      ping: vi.fn().mockResolvedValue('pong'),
      getBackendStatus: vi.fn().mockResolvedValue('checking'),
      getDbStatus: vi.fn().mockResolvedValue({ status: 'managed', chroma_collections: {}, redis_ping_ms: null, object_store_buckets: {}, memory_vertices: 0, memory_edges: 0, last_recall_timestamp: null }),
      quadAnalysisStatus: vi.fn().mockResolvedValue({ pod_count: 0, collective_confidence: 0, mode: 'idle' }),
      dmrfStatus: vi.fn().mockResolvedValue({ status: 'idle', tier: null, frost_depth: null, run_id: null, tier_counts: {} }),
      dsqpPersonaProfiles: vi.fn().mockResolvedValue({ success: true, profiles: [], partial: false, failures: {} }),
      getNetworkStatus: vi.fn().mockResolvedValue({ state: 'ONLINE', last_checked: '2026-05-28T00:00:00Z', active_provider: 'openai' }),
      getLocalModelStatus: vi.fn().mockResolvedValue({ ollama_available: false, models_installed: [], active_model: null }),
      getReasoningLayerProgress: vi.fn().mockResolvedValue({ active_run_id: null, status: 'idle', current_layer: null, layer_name: null, kas_running: [], confidence_so_far: null, persona_confidences: [], frost_snapshot_count: 0, updated_at: new Date().toISOString() }),
      getKAExecutionFeed: vi.fn().mockResolvedValue({ items: [], limit: 20, updated_at: new Date().toISOString() }),
      getDesktopStorageMetrics: vi.fn().mockResolvedValue(null),
      chooseBackupFolder: vi.fn().mockResolvedValue(null),
      runDatabaseBackup: vi.fn().mockResolvedValue({ artifact_path: '', size_bytes: 0, manifest: {} }),
      getUpdateState: vi.fn().mockResolvedValue(idleUpdateState),
      checkForUpdates: vi.fn().mockResolvedValue(idleUpdateState),
      downloadUpdate: vi.fn().mockResolvedValue(idleUpdateState),
      onBackendLog: vi.fn(() => () => undefined),
      onBackendError: vi.fn(() => () => undefined),
    };
  });

  afterEach(() => {
    vi.clearAllTimers();
    delete (window as any).electronAPI;
  });

  it('initially renders nothing if not yet detected as desktop', () => {
    const { container } = render(<DesktopStatus />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders status panel when detected as desktop', async () => {
    render(<DesktopStatus />);
    
    // Fast-forward to trigger setIsDesktop(true)
    await act(async () => {
      vi.advanceTimersByTime(0);
    });
    
    // Allow state updates to settle
    await act(async () => {
         await Promise.resolve();
    });

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Desktop Engine')).toBeInTheDocument();
  });

  it('shows running status correctly', async () => {
    window.electronAPI!.getBackendStatus = vi.fn().mockResolvedValue('running');

    render(<DesktopStatus />);
    
    await act(async () => {
      vi.advanceTimersByTime(0);
    });

    // Need to wait for the async checkStatus call to resolve and setState
    // Since checkStatus is called immediately, we can wait for next tick or mock promise resolution
    // Ren-run timers for the interval check as well
    await act(async () => {
        // Force promise resolution cycle
        await Promise.resolve();
    });

    expect(screen.getByText('Online')).toBeInTheDocument();
  });

  it('handles offline/error status', async () => {
    window.electronAPI!.getBackendStatus = vi.fn().mockRejectedValue(new Error('Failed'));

    render(<DesktopStatus />);
    
    await act(async () => {
        vi.advanceTimersByTime(0);
        // Advance past interval
        vi.advanceTimersByTime(6000); 
    });

    expect(screen.getByText('Offline')).toBeInTheDocument();
  });

  it('displays logs from electronAPI', async () => {
    let capturedCallback: ElectronLogHandler | undefined;
    
    window.electronAPI!.onBackendLog = (cb) => {
      capturedCallback = cb;
      return () => undefined;
    };

    render(<DesktopStatus />);
    
    await act(async () => {
      vi.advanceTimersByTime(0);
    });

    await act(async () => {
      if (capturedCallback) {
        capturedCallback('System initialized');
        capturedCallback('Database connected');
      }
    });

    expect(screen.getByText('System initialized')).toBeInTheDocument();
    expect(screen.getByText('Database connected')).toBeInTheDocument();
  });

  it('does not auto-load DSQP persona profiles while polling status', async () => {
    window.electronAPI!.getBackendStatus = vi.fn().mockResolvedValue('running');
    window.electronAPI!.dsqpPersonaProfiles = vi.fn();

    render(<DesktopStatus />);

    await act(async () => {
      vi.advanceTimersByTime(0);
      await Promise.resolve();
    });

    await act(async () => {
      vi.advanceTimersByTime(5000);
      await Promise.resolve();
    });

    expect(window.electronAPI!.dsqpPersonaProfiles).not.toHaveBeenCalled();
  });

  it('shows network details for a running backend', async () => {
    window.electronAPI!.getBackendStatus = vi.fn().mockResolvedValue('running');
    window.electronAPI!.getNetworkStatus = vi.fn().mockResolvedValue({ state: 'ONLINE', last_checked: '2026-05-28T00:00:00Z' });

    render(<DesktopStatus />);

    await act(async () => {
      vi.advanceTimersByTime(0);
      await Promise.resolve();
    });

    expect(screen.getByText('ONLINE')).toBeInTheDocument();
  });

  it('can minimize and restore the status panel', async () => {
    window.electronAPI!.getBackendStatus = vi.fn().mockResolvedValue('running');

    render(<DesktopStatus />);

    await act(async () => {
      vi.advanceTimersByTime(0);
      await Promise.resolve();
    });

    fireEvent.click(screen.getByRole('button', { name: /minimize desktop engine panel/i }));
    expect(screen.getByRole('button', { name: /show desktop engine status/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /show desktop engine status/i }));
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});

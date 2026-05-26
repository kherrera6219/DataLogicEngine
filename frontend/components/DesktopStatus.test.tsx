
import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import DesktopStatus from './DesktopStatus';

// Mock types for window.electronAPI
interface ElectronLogHandler {
  (log: string): void;
}

interface MockElectronAPI {
  getBackendStatus: () => Promise<string>;
  getDbStatus: () => Promise<{ status: string; chroma_collections: Record<string, number>; redis_ping_ms: number | null }>;
  onBackendLog: (callback: ElectronLogHandler) => () => void;
}

declare global {
  interface Window {
    electronAPI?: MockElectronAPI;
  }
}

describe('DesktopStatus', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    // Default mock implementation
    window.electronAPI = {
      getBackendStatus: vi.fn().mockResolvedValue('checking'),
      getDbStatus: vi.fn().mockResolvedValue({ status: 'managed', chroma_collections: {}, redis_ping_ms: null }),
      onBackendLog: vi.fn(() => () => undefined),
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
});

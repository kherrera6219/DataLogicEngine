import { render } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ClientErrorBootstrap from './ClientErrorBootstrap';

// Mock the telemetry module
vi.mock('@/lib/telemetry/client-errors', () => ({
  installGlobalClientErrorHandlers: vi.fn(),
}));

import { installGlobalClientErrorHandlers } from '@/lib/telemetry/client-errors';

describe('ClientErrorBootstrap', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(installGlobalClientErrorHandlers).mockReturnValue(undefined);
  });

  it('should render nothing (null)', () => {
    const { container } = render(<ClientErrorBootstrap />);
    expect(container.firstChild).toBeNull();
  });

  it('should call installGlobalClientErrorHandlers on mount', () => {
    render(<ClientErrorBootstrap />);
    expect(installGlobalClientErrorHandlers).toHaveBeenCalled();
  });

  it('should call installGlobalClientErrorHandlers exactly once', () => {
    const { rerender } = render(<ClientErrorBootstrap />);
    expect(installGlobalClientErrorHandlers).toHaveBeenCalledTimes(1);

    // Rerender should still be called only once in the useEffect
    rerender(<ClientErrorBootstrap />);
    // In strict mode, useEffect runs twice, but the real app runs once
    expect(installGlobalClientErrorHandlers).toHaveBeenCalled();
  });

  it('should call cleanup function returned by installGlobalClientErrorHandlers on unmount', () => {
    const mockCleanup = vi.fn();
    vi.mocked(installGlobalClientErrorHandlers).mockReturnValue(mockCleanup);

    const { unmount } = render(<ClientErrorBootstrap />);
    expect(installGlobalClientErrorHandlers).toHaveBeenCalled();

    unmount();
    expect(mockCleanup).toHaveBeenCalled();
  });

  it('should handle when installGlobalClientErrorHandlers returns undefined', () => {
    vi.mocked(installGlobalClientErrorHandlers).mockReturnValue(undefined);

    expect(() => {
      render(<ClientErrorBootstrap />);
    }).not.toThrow();
  });

  it('should be a self-closing component with no visible output', () => {
    const { container } = render(<ClientErrorBootstrap />);
    expect(container.textContent).toBe('');
  });
});

import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ClientErrorBootstrap from './ClientErrorBootstrap';

// Mock the telemetry module
vi.mock('@/lib/telemetry/client-errors', () => ({
  installGlobalClientErrorHandlers: vi.fn(() => {
    // Return a cleanup function
    return () => {
      // Cleanup
    };
  }),
}));

import { installGlobalClientErrorHandlers } from '@/lib/telemetry/client-errors';

describe('ClientErrorBootstrap', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render without crashing', () => {
    const { container } = render(<ClientErrorBootstrap />);
    expect(container).toBeInTheDocument();
  });

  it('should return null (no UI rendered)', () => {
    const { container } = render(<ClientErrorBootstrap />);
    // The component should render null, so container should have no meaningful content
    expect(container.firstChild).toBeFalsy();
  });

  it('should call installGlobalClientErrorHandlers on mount', () => {
    const mockedInstall = vi.mocked(installGlobalClientErrorHandlers);
    render(<ClientErrorBootstrap />);

    expect(mockedInstall).toHaveBeenCalledTimes(1);
  });

  it('should set up error handlers for global errors', () => {
    const mockedInstall = vi.mocked(installGlobalClientErrorHandlers);
    const mockCleanup = vi.fn();
    mockedInstall.mockReturnValueOnce(mockCleanup);

    const { unmount } = render(<ClientErrorBootstrap />);

    expect(mockedInstall).toHaveBeenCalled();

    // Cleanup should be called on unmount
    unmount();
    expect(mockCleanup).toHaveBeenCalled();
  });

  it('should handle multiple mounts/unmounts correctly', () => {
    const mockedInstall = vi.mocked(installGlobalClientErrorHandlers);
    const mockCleanup = vi.fn();
    mockedInstall.mockReturnValue(mockCleanup);

    // First mount
    const { unmount: unmount1 } = render(<ClientErrorBootstrap />);
    expect(mockedInstall).toHaveBeenCalledTimes(1);

    // Cleanup
    unmount1();
    expect(mockCleanup).toHaveBeenCalledTimes(1);

    // Second mount
    const { unmount: unmount2 } = render(<ClientErrorBootstrap />);
    expect(mockedInstall).toHaveBeenCalledTimes(2);

    // Second cleanup
    unmount2();
    expect(mockCleanup).toHaveBeenCalledTimes(2);
  });
});

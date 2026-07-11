import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, it, expect, vi } from 'vitest';
import { CloudStatusIndicator } from './cloud-status-indicator';

const { requestMock } = vi.hoisted(() => ({ requestMock: vi.fn() }));

vi.mock('@/lib/api/client', () => ({ request: requestMock }));

describe('CloudStatusIndicator', () => {
  beforeEach(() => {
    requestMock.mockReset();
    requestMock.mockResolvedValue({ status: 'ok' });
  });

  it('should render initial loading state', () => {
    render(<CloudStatusIndicator />);
    // Checking Status is in the title attribute
    const indicator = screen.getByTitle(/Checking Status/i);
    expect(indicator).toBeInTheDocument();
  });

  it('shows available only after the health endpoint responds successfully', async () => {
    render(<CloudStatusIndicator />);
    
    await waitFor(() => {
        expect(screen.getByTitle(/Available/i)).toBeInTheDocument();
    });
    expect(requestMock).toHaveBeenCalledWith('/health');
  });

  it('shows degraded when a checked backend component is unavailable', async () => {
    requestMock.mockResolvedValue({ status: 'degraded' });
    render(<CloudStatusIndicator />);
    await waitFor(() => expect(screen.getByTitle(/Degraded/i)).toBeInTheDocument());
  });

  it('shows offline when the health request fails', async () => {
    requestMock.mockRejectedValue(new Error('offline'));
    render(<CloudStatusIndicator />);
    await waitFor(() => expect(screen.getByTitle(/Offline/i)).toBeInTheDocument());
  });

  it('should show processing state when prop is true', () => {
    render(<CloudStatusIndicator isProcessing={true} />);
    // "Cloud processing" is visible in sm and up, but hidden sm:inline might be tricky in JSDOM
    // We can check by text if JSDOM renders it
    expect(screen.getByText(/Cloud processing/i)).toBeInTheDocument();
  });
});

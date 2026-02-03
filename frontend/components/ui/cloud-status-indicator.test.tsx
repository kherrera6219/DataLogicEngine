import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { CloudStatusIndicator } from './cloud-status-indicator';

describe('CloudStatusIndicator', () => {
  it('should render initial loading state', () => {
    render(<CloudStatusIndicator />);
    expect(screen.getByText('Checking Status...')).toBeInTheDocument();
  });

  it('should transition to online state after delay', async () => {
    render(<CloudStatusIndicator />);
    
    await waitFor(() => {
        expect(screen.getByText('LLM Gateway: Operational')).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('should show processing state when prop is true', () => {
    render(<CloudStatusIndicator isProcessing={true} />);
    expect(screen.getByText('Cloud processing')).toBeInTheDocument();
    expect(screen.getByText(/A cloud reasoning task is currently in progress/i, { exact: false })).toBeInTheDocument();
  });
});

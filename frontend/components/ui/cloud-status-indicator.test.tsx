import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { CloudStatusIndicator } from './cloud-status-indicator';

describe('CloudStatusIndicator', () => {
  it('should render initial loading state', () => {
    render(<CloudStatusIndicator />);
    // Checking Status is in the title attribute
    const indicator = screen.getByTitle(/Checking Status/i);
    expect(indicator).toBeInTheDocument();
  });

  it('should transition to online state after delay', async () => {
    render(<CloudStatusIndicator />);
    
    await waitFor(() => {
        expect(screen.getByTitle(/Operational/i)).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('should show processing state when prop is true', () => {
    render(<CloudStatusIndicator isProcessing={true} />);
    // "Cloud processing" is visible in sm and up, but hidden sm:inline might be tricky in JSDOM
    // We can check by text if JSDOM renders it
    expect(screen.getByText(/Cloud processing/i)).toBeInTheDocument();
  });
});

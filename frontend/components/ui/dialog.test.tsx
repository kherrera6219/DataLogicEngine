import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Dialog, DialogTrigger, DialogContent, DialogTitle, DialogDescription } from './dialog';

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

describe('Dialog', () => {
  it('should render trigger and open content', async () => {
    render(
      <Dialog>
        <DialogTrigger>Open Dialog</DialogTrigger>
        <DialogContent>
          <DialogTitle>Dialog Title</DialogTitle>
          <DialogDescription>Dialog Description</DialogDescription>
        </DialogContent>
      </Dialog>
    );

    const trigger = screen.getByText('Open Dialog');
    expect(trigger).toBeInTheDocument();
    
    // Content should not be visible initially
    expect(screen.queryByText('Dialog Title')).not.toBeInTheDocument();

    fireEvent.click(trigger);

    await waitFor(() => {
      expect(screen.getByText('Dialog Title')).toBeInTheDocument();
      expect(screen.getByText('Dialog Description')).toBeInTheDocument();
    });
  });
});

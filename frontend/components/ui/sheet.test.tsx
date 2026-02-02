import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Sheet, SheetTrigger, SheetContent, SheetTitle, SheetDescription } from './sheet';

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

describe('Sheet', () => {
  it('should render trigger and open sheet', async () => {
    render(
      <Sheet>
        <SheetTrigger>Open Sheet</SheetTrigger>
        <SheetContent>
          <SheetTitle>Sheet Title</SheetTitle>
          <SheetDescription>Sheet Description</SheetDescription>
        </SheetContent>
      </Sheet>
    );

    fireEvent.click(screen.getByText('Open Sheet'));

    await waitFor(() => {
      expect(screen.getByText('Sheet Title')).toBeInTheDocument();
    });
  });
});

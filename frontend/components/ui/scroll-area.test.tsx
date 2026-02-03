import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ScrollArea } from './scroll-area';

// Mock ResizeObserver which is used by Radix ScrollArea
global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
}));

describe('ScrollArea', () => {
  it('should render children', () => {
    render(
      <ScrollArea className="h-[200px]">
        <div data-testid="content">Deep Content</div>
      </ScrollArea>
    );
    expect(screen.getByTestId('content')).toBeInTheDocument();
  });
});

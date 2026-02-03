import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AdvancedControls } from './AdvancedControls';

// Mock UI components
vi.mock('@/components/ui/sheet', () => ({
  Sheet: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SheetTrigger: ({ children }: { children: React.ReactNode }) => <div data-testid="sheet-trigger">{children}</div>,
  SheetContent: ({ children }: { children: React.ReactNode }) => <div data-testid="sheet-content">{children}</div>,
  SheetHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SheetTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  SheetDescription: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/slider', () => ({
  Slider: () => (
    <input
      type="range"
      data-testid="slider"
      title="Enhancement Level"
      aria-label="Enhancement Level"
    />
  ),
}));

vi.mock('@/components/ui/switch', () => ({
  Switch: () => (
    <input
      type="checkbox"
      data-testid="switch"
      title="Toggle Feature"
      aria-label="Toggle Feature"
    />
  ),
}));

describe('AdvancedControls', () => {
  it('should render trigger button', () => {
    render(<AdvancedControls />);
    expect(screen.getByTestId('sheet-trigger')).toBeInTheDocument();
  });

  it('should render configuration content', () => {
    render(<AdvancedControls />);
    expect(screen.getByText('Enhancement Level')).toBeInTheDocument();
    expect(screen.getByText('Persona Weights')).toBeInTheDocument();
  });
});

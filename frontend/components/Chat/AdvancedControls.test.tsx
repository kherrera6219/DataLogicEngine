import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AdvancedControls } from './AdvancedControls';

// Mock UI components
vi.mock('@/components/ui/sheet', () => ({
  Sheet: ({ children }) => <div>{children}</div>,
  SheetTrigger: ({ children }) => <div data-testid="sheet-trigger">{children}</div>,
  SheetContent: ({ children }) => <div data-testid="sheet-content">{children}</div>,
  SheetHeader: ({ children }) => <div>{children}</div>,
  SheetTitle: ({ children }) => <div>{children}</div>,
  SheetDescription: ({ children }) => <div>{children}</div>,
}));

vi.mock('@/components/ui/slider', () => ({
  Slider: () => <input type="range" data-testid="slider" />
}));

vi.mock('@/components/ui/switch', () => ({
  Switch: () => <input type="checkbox" data-testid="switch" />
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

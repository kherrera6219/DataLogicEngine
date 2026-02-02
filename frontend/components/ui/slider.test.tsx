import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Slider } from './slider';

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

describe('Slider', () => {
  it('should render', () => {
    render(<Slider defaultValue={[50]} max={100} step={1} />);
    expect(screen.getByRole('slider')).toBeInTheDocument();
  });
});

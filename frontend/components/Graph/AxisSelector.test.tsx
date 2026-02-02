import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AxisSelector, AXIS_NAMES } from './AxisSelector';

describe('AxisSelector', () => {
  it('should render all axis names', () => {
    const handleChange = vi.fn();
    render(<AxisSelector activeAxis={1} onChange={handleChange} />);
    
    AXIS_NAMES.forEach(name => {
      expect(screen.getByText(name)).toBeInTheDocument();
    });
  });

  it('should indicate active axis', () => {
    const handleChange = vi.fn();
    render(<AxisSelector activeAxis={1} onChange={handleChange} />);
    
    const firstTab = screen.getAllByRole('tab')[0];
    expect(firstTab).toHaveAttribute('aria-selected', 'true');
  });

  it('should call onChange when clicked', () => {
    const handleChange = vi.fn();
    render(<AxisSelector activeAxis={1} onChange={handleChange} />);
    
    const secondButton = screen.getByText('Sectors').closest('button');
    if (secondButton) fireEvent.click(secondButton);
    expect(handleChange).toHaveBeenCalledWith(2);
  });
});

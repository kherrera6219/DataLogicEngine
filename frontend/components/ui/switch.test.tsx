import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Switch } from './switch';

describe('Switch', () => {
  it('should render', () => {
    render(<Switch data-testid="switch" />);
    expect(screen.getByTestId('switch')).toBeInTheDocument();
  });

  it('should toggle state', () => {
    const handleChange = vi.fn();
    render(<Switch checked={false} onCheckedChange={handleChange} role="switch" />);
    const switchEl = screen.getByRole('switch');
    expect(switchEl).toHaveAttribute('aria-checked', 'false');
    
    fireEvent.click(switchEl);
    expect(handleChange).toHaveBeenCalledWith(true);
  });
});

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Label } from './label';

describe('Label', () => {
  it('should render correctly', () => {
    render(<Label>Test Label</Label>);
    expect(screen.getByText('Test Label')).toBeInTheDocument();
  });

  it('should accept custom class names', () => {
    render(<Label className="custom-label">Test Label</Label>);
    expect(screen.getByText('Test Label')).toHaveClass('custom-label');
  });
});

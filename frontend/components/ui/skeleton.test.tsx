import { render } from '@testing-library/react';
import { expect, test, describe } from 'vitest';
import { Skeleton } from './skeleton';
import React from 'react';

describe('Skeleton', () => {
  test('renders with default pulse animation', () => {
    const { container } = render(<Skeleton />);
    expect(container.firstChild).toHaveClass('animate-pulse');
    expect(container.firstChild).toHaveClass('bg-muted/50');
  });

  test('applies custom class names for sizing', () => {
    const { container } = render(<Skeleton className="w-[100px] h-4" />);
    expect(container.firstChild).toHaveClass('w-[100px]');
    expect(container.firstChild).toHaveClass('h-4');
  });

  test('passes additional HTML attributes', () => {
    const { container } = render(<Skeleton data-testid="skeleton-test" aria-label="Loading..." />);
    expect(container.querySelector('[data-testid="skeleton-test"]')).toBeDefined();
    expect(container.firstChild).toHaveAttribute('aria-label', 'Loading...');
  });
});

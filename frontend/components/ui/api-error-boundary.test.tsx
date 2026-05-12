import React, { useState } from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterAll } from 'vitest';
import { ApiErrorBoundary } from './api-error-boundary';

// Silencing console.error for expected failures
const originalConsoleError = console.error;
beforeEach(() => {
  console.error = vi.fn();
});

afterAll(() => {
  console.error = originalConsoleError;
});

const ThrowError = ({ shouldThrow = true }: { shouldThrow?: boolean }) => {
  if (shouldThrow) {
    throw new Error('Test Error');
  }
  return <div data-testid="recovered">Recovered</div>;
};

describe('ApiErrorBoundary', () => {
  it('should render children when no error occurs', () => {
    render(
      <ApiErrorBoundary>
        <div data-testid="child">Normal Content</div>
      </ApiErrorBoundary>
    );
    expect(screen.getByTestId('child')).toBeInTheDocument();
  });

  it('should render fallback UI when an error occurs', () => {
    render(
      <ApiErrorBoundary>
        <ThrowError />
      </ApiErrorBoundary>
    );
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByText(/module failed to load/i)).toBeInTheDocument();
  });

  it('should render custom fallback if provided', () => {
    render(
      <ApiErrorBoundary fallback={<div data-testid="custom-fallback">Error!</div>}>
        <ThrowError />
      </ApiErrorBoundary>
    );
    expect(screen.getByTestId('custom-fallback')).toBeInTheDocument();
  });

  it('should display module name in error message', () => {
    render(
      <ApiErrorBoundary moduleName="Compliance Engine">
        <ThrowError />
      </ApiErrorBoundary>
    );
    expect(screen.getByText('Compliance Engine')).toBeInTheDocument();
  });

  it('should allow retrying via Try again button', () => {
    const TestWrapper = () => {
      const [shouldThrow, setShouldThrow] = useState(true);
      return (
        <div>
          <button data-testid="fix-it" onClick={() => setShouldThrow(false)}>Fix It</button>
          <ApiErrorBoundary>
            <ThrowError shouldThrow={shouldThrow} />
          </ApiErrorBoundary>
        </div>
      );
    };

    render(<TestWrapper />);

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();

    // Fix the error state first
    fireEvent.click(screen.getByTestId('fix-it'));

    // Now click Try again
    const retryBtn = screen.getByText('Try again');
    fireEvent.click(retryBtn);

    expect(screen.getByTestId('recovered')).toBeInTheDocument();
  });
});

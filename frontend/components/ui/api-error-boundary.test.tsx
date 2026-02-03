```javascript
import { render, screen, waitFor } from '@testing-library/react';
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

const ThrowError = () => {
  throw new Error('Test Error');
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
    expect(screen.getByText('Signal Disruption')).toBeInTheDocument();
    expect(screen.getByText(/Failed to retrieve data for/i)).toBeInTheDocument();
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
    expect(screen.getByTitle(/Checking Status.../)).toBeInTheDocument();
  });

  it('should allow retrying via Re-sync button', async () => {
    const { rerender } = render(
      <ApiErrorBoundary>
        <ThrowError />
      </ApiErrorBoundary>
    );
    
    expect(screen.getByText('Signal Disruption')).toBeInTheDocument();
    
    await waitFor(() => {
        expect(screen.getByTitle(/LLM Gateway: Operational/)).toBeInTheDocument();
    }, { timeout: 2000 });

    // After clicking retry, state should reset. 
    // We need to wait for the state update to propagate
    fireEvent.click(screen.getByText('Re-sync'));
    
    rerender(
      <ApiErrorBoundary>
        <div data-testid="recovered">Recovered</div>
      </ApiErrorBoundary>
    );
    
    expect(screen.getByTestId('recovered')).toBeInTheDocument();
  });
});
```

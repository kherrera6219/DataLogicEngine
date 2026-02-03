import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ToastProvider, useToast } from './use-toast';

const TestComponent = () => {
  const { toast } = useToast();
  return (
    <button onClick={() => toast('Test Message', 'success', 1000)}>
      Show Toast
    </button>
  );
};

describe('Toast System', () => {
  it('should show toast when triggered', async () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );
    
    fireEvent.click(screen.getByText('Show Toast'));
    
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Test Message')).toBeInTheDocument();
  });

  it('should remove toast after duration', async () => {
    vi.useFakeTimers();
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );
    
    fireEvent.click(screen.getByText('Show Toast'));
    expect(screen.getByRole('alert')).toBeInTheDocument();
    
    act(() => {
      vi.advanceTimersByTime(1100);
    });
    
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    vi.useRealTimers();
  });

  it('should allow manual closing of toast', async () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );
    
    fireEvent.click(screen.getByText('Show Toast'));
    const closeBtn = screen.getByLabelText('Close notification');
    
    fireEvent.click(closeBtn);
    
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('should throw error if useToast is used outside provider', () => {
    // Suppress console.error for this expected error
    vi.spyOn(console, 'error').mockImplementation(() => {});
    
    expect(() => render(<TestComponent />)).toThrow('useToast must be used within a ToastProvider');
  });
});

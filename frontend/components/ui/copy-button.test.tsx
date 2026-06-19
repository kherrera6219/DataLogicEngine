import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CopyButton } from './copy-button';

// Mock useToast
const mockToast = vi.fn();
vi.mock('./use-toast', () => ({
  useToast: () => ({ toast: mockToast })
}));

describe('CopyButton', () => {
  const text = 'Hello World';

  beforeEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
    // Mock navigator.clipboard
    Object.assign(navigator, {
      clipboard: {
        writeText: vi.fn().mockImplementation(() => Promise.resolve()),
      },
    });
  });

  it('should render copy icon initially', () => {
    render(<CopyButton text={text} />);
    expect(screen.getByLabelText('Copy response to clipboard')).toBeInTheDocument();
  });

  it('should copy text and show success state', async () => {
    vi.useFakeTimers();
    render(<CopyButton text={text} />);
    const button = screen.getByRole('button');
    
    await act(async () => {
      fireEvent.click(button);
      await Promise.resolve();
    });
    
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(text);

    expect(screen.getByLabelText('Copied to clipboard')).toBeInTheDocument();
    expect(mockToast).toHaveBeenCalledWith("Response copied to clipboard", "success", 2000);

    await act(async () => {
      vi.advanceTimersByTime(2000);
    });

    expect(screen.getByLabelText('Copy response to clipboard')).toBeInTheDocument();
  });

  it('should handle copy failure', async () => {
    (navigator.clipboard.writeText as any).mockImplementationOnce(() => Promise.reject(new Error()));
    
    render(<CopyButton text={text} />);
    fireEvent.click(screen.getByRole('button'));
    
    await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith("Failed to copy text", "error", 2000);
    });
  });
});

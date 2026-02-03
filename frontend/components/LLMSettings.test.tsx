
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import LLMSettings from './LLMSettings';
import { useAuth } from '@/contexts/AuthContext';

// Mock dependencies
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('LLMSettings', () => {
  const mockUser = {
    id: 'user-1',
    role: 'admin',
    windows_sid: 'S-1-5-21-mock-sid',
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (useAuth as any).mockReturnValue({ user: mockUser });
  });

  it('renders correctly with user context', () => {
    render(<LLMSettings />);
    
    expect(screen.getByText('LLM Configuration')).toBeInTheDocument();
    expect(screen.getByText('Windows Native Identity')).toBeInTheDocument();
    expect(screen.getByText('S-1-5-21-mock-sid')).toBeInTheDocument();
    expect(screen.getByText('UKG admin')).toBeInTheDocument();
  });

  it('handles provider selection change', () => {
    render(<LLMSettings />);
    
    const select = screen.getByTitle('LLM Provider Selector');
    fireEvent.change(select, { target: { value: 'anthropic' } });
    
    expect(select).toHaveValue('anthropic');
  });

  it('handles API key input', () => {
    render(<LLMSettings />);
    
    const input = screen.getByLabelText('API Key');
    fireEvent.change(input, { target: { value: 'sk-test-key' } });
    
    expect(input).toHaveValue('sk-test-key');
  });

  it('submits API key successfully', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    });

    render(<LLMSettings />);
    
    const input = screen.getByLabelText('API Key');
    fireEvent.change(input, { target: { value: 'sk-test-key' } });
    
    const saveButton = screen.getByRole('button', { name: /Save Securely/i });
    fireEvent.click(saveButton);

    expect(screen.getByText(/Saving Encrypted Key/i)).toBeInTheDocument();

    await waitFor(() => {
        expect(screen.getByText('API Key saved securely via Windows DPAPI')).toBeInTheDocument();
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/v1/gateway/keys', expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: 'openai', key: 'sk-test-key' }),
    }));
  });

  it('handles submission error handles failure response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ message: 'Invalid key format' }),
    });

    render(<LLMSettings />);
    
    const input = screen.getByLabelText('API Key');
    fireEvent.change(input, { target: { value: 'bad-key' } });
    
    const saveButton = screen.getByRole('button', { name: /Save Securely/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
        expect(screen.getByText('Invalid key format')).toBeInTheDocument();
    });
  });

  it('handles network error during submission', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network Error'));

    render(<LLMSettings />);
    
    const input = screen.getByLabelText('API Key');
    fireEvent.change(input, { target: { value: 'sk-fail' } });
    
    const saveButton = screen.getByRole('button', { name: /Save Securely/i });
    fireEvent.click(saveButton);

    await waitFor(() => {
        expect(screen.getByText('Network error while saving key')).toBeInTheDocument();
    });
  });
});

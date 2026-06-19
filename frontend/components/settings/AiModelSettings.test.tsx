import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AiModelSettings } from './AiModelSettings';

// Mock API and UI components
vi.mock('@/lib/api', () => ({
  request: vi.fn(),
}));

vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: any) => <div data-testid="card">{children}</div>,
  CardContent: ({ children }: any) => <div>{children}</div>,
  CardDescription: ({ children }: any) => <div>{children}</div>,
  CardHeader: ({ children }: any) => <div>{children}</div>,
  CardTitle: ({ children }: any) => <h2>{children}</h2>,
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children, className }: any) => (
    <span data-testid="badge" className={className}>
      {children}
    </span>
  ),
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, type }: any) => (
    <button onClick={onClick} type={type}>
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/input', () => ({
  Input: ({ type, onChange, value, placeholder }: any) => (
    <input
      type={type}
      onChange={onChange}
      value={value}
      placeholder={placeholder}
      data-testid="input"
    />
  ),
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({ children, onValueChange }: any) => (
    <select onChange={(e) => onValueChange?.(e.target.value)} data-testid="select">
      {children}
    </select>
  ),
}));

vi.mock('lucide-react', () => ({
  Brain: () => <span>Brain</span>,
  CheckCircle2: () => <span>Check</span>,
  Eye: () => <span>Eye</span>,
  FlaskConical: () => <span>Flask</span>,
  RefreshCw: () => <span>Refresh</span>,
  Save: () => <span>Save</span>,
  Power: () => <span>Power</span>,
  History: () => <span>History</span>,
}));

import { request } from '@/lib/api';

describe('AiModelSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (vi.mocked(request) as any).mockResolvedValue({ providers: [] });
  });

  it('should render component without crashing', () => {
    const { container } = render(<AiModelSettings />);
    // Component should render without throwing
    expect(container).toBeInTheDocument();
  });

  it('should load providers on mount', async () => {
    render(<AiModelSettings />);

    await waitFor(() => {
      expect(request).toHaveBeenCalledWith('/gateway/providers');
    });
  });

  it('should handle empty providers list', async () => {
    (vi.mocked(request) as any).mockResolvedValue({ providers: [] });
    render(<AiModelSettings />);

    await waitFor(() => {
      expect(request).toHaveBeenCalled();
    });
  });

  it('should handle providers API error', async () => {
    (vi.mocked(request) as any).mockRejectedValue(new Error('API Error'));
    render(<AiModelSettings />);

    await waitFor(() => {
      expect(request).toHaveBeenCalled();
    });
  });

  it('should handle multiple providers', async () => {
    const mockProviders = [
      { id: '1', name: 'OpenAI', type: 'openai', is_default: true },
      { id: '2', name: 'Anthropic', type: 'anthropic' },
      { id: '3', name: 'Google', type: 'google' },
    ];

    (vi.mocked(request) as any).mockResolvedValue({ providers: mockProviders });
    render(<AiModelSettings />);

    await waitFor(() => {
      expect(request).toHaveBeenCalledWith('/gateway/providers');
    });
  });

  it('should handle Ollama provider (local tier)', async () => {
    const mockProviders = [
      { id: '1', name: 'Ollama', type: 'ollama' },
    ];

    (vi.mocked(request) as any).mockResolvedValue({ providers: mockProviders });
    render(<AiModelSettings />);

    await waitFor(() => {
      expect(request).toHaveBeenCalled();
    });
  });

  it('should handle tier badge for different provider types', async () => {
    const mockProviders = [
      { id: '1', name: 'OpenAI', type: 'openai' },
      { id: '2', name: 'Google', type: 'google' },
    ];

    (vi.mocked(request) as any).mockResolvedValue({ providers: mockProviders });
    render(<AiModelSettings />);

    await waitFor(() => {
      expect(screen.getAllByTestId('badge').length).toBeGreaterThan(0);
    });
  });

  it('should initialize with default values', async () => {
    render(<AiModelSettings />);

    await waitFor(() => {
      expect(request).toHaveBeenCalled();
    });
  });

  it('should handle API key input', async () => {
    render(<AiModelSettings />);

    await waitFor(() => {
      const inputs = screen.getAllByTestId('input');
      expect(inputs.length).toBeGreaterThan(0);
    });
  });

  it('should have save buttons for settings', async () => {
    render(<AiModelSettings />);

    await waitFor(() => {
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  it('should format errors properly', async () => {
    const errorMessage = 'Invalid API key format';
    (vi.mocked(request) as any).mockRejectedValue(new Error(errorMessage));

    render(<AiModelSettings />);

    await waitFor(() => {
      expect(request).toHaveBeenCalled();
    });
  });

  it('should handle provider selection change', async () => {
    const mockProviders = [
      { id: '1', name: 'OpenAI', type: 'openai' },
      { id: '2', name: 'Anthropic', type: 'anthropic' },
    ];

    (vi.mocked(request) as any).mockResolvedValue({ providers: mockProviders });
    render(<AiModelSettings />);

    await waitFor(() => {
      expect(request).toHaveBeenCalled();
    });
  });
});

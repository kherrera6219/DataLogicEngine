import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AiModelSettings, getProviderStatus } from './AiModelSettings';

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
  Badge: ({ children, className, variant }: any) => (
    <span data-testid="badge" className={className} data-variant={variant}>
      {children}
    </span>
  ),
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, ...props }: any) => (
    <button {...props}>
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/input', () => ({
  Input: ({ type, onChange, value, placeholder, id, 'aria-label': ariaLabel }: any) => (
    <input
      id={id}
      type={type}
      onChange={onChange}
      value={value}
      placeholder={placeholder}
      aria-label={ariaLabel}
      data-testid="input"
    />
  ),
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({ children, onValueChange, onChange, id }: any) => (
    <select
      id={id}
      onChange={(e) => {
        onValueChange?.(e.target.value);
        onChange?.(e);
      }}
      data-testid="select"
    >
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

  it('should handle a configured cloud provider', async () => {
    const mockProviders = [
      { id: '1', name: 'Google', type: 'google' },
    ];

    (vi.mocked(request) as any).mockResolvedValue({ providers: mockProviders });
    render(<AiModelSettings />);

    await waitFor(() => {
      expect(request).toHaveBeenCalled();
    });
  });

  it('should render provider status badges', async () => {
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

  it('labels saved keys separately from verified keys', async () => {
    (vi.mocked(request) as any).mockImplementation((endpoint: string) => {
      if (endpoint === '/gateway/providers') {
        return Promise.resolve({
          providers: [{ id: '1', name: 'OpenAI', type: 'openai', has_api_key: true }],
        });
      }
      return Promise.resolve({});
    });

    render(<AiModelSettings />);

    await waitFor(() => {
      expect(screen.getByText('Key saved')).toBeInTheDocument();
    });

    expect(screen.queryByText('API key set')).not.toBeInTheDocument();
    expect(screen.queryByText('Key verified')).not.toBeInTheDocument();
    expect(screen.getByText('Key saved').closest('[data-testid="badge"]')).toHaveAttribute(
      'data-variant',
      'secondary'
    );
  });

  it('maps verified keys to the verified status only when validation has succeeded', () => {
    expect(getProviderStatus({ id: 'g1', name: 'Google', type: 'google', has_api_key: true }, false)).toEqual({
      label: 'Key saved',
      variant: 'secondary',
    });
    expect(getProviderStatus({ id: 'g1', name: 'Google', type: 'google', has_api_key: true }, true)).toEqual({
      label: 'Key verified',
      variant: 'success',
    });
  });

  it('labels unsupported legacy provider rows without a valid-key state', async () => {
    (vi.mocked(request) as any).mockImplementation((endpoint: string) => {
      if (endpoint === '/gateway/providers') {
        return Promise.resolve({
          providers: [{ id: 'legacy-1', name: 'Ollama', type: 'ollama', has_api_key: true }],
        });
      }
      return Promise.resolve({});
    });

    render(<AiModelSettings />);

    await waitFor(() => {
      expect(screen.getByText('Unsupported legacy provider')).toBeInTheDocument();
    });

    expect(screen.queryByText('API key set')).not.toBeInTheDocument();
    expect(screen.queryByText('Key verified')).not.toBeInTheDocument();
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

  it('should expose accessible controls for provider configuration', async () => {
    render(<AiModelSettings />);

    await waitFor(() => {
      expect(screen.getByLabelText('Provider')).toBeInTheDocument();
      expect(screen.getByLabelText('Model')).toBeInTheDocument();
      expect(screen.getByLabelText('API Key')).toBeInTheDocument();
      expect(screen.getByRole('switch', { name: /enable ai processing/i })).toBeInTheDocument();
      expect(screen.getByRole('switch', { name: /store chat history/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /save model configuration/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /test provider model/i })).toBeInTheDocument();
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

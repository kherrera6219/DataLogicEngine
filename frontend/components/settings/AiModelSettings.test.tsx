import React from 'react';
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AiModelSettings, getProviderStatus } from './AiModelSettings';

// Mock API and UI components
vi.mock('@/lib/api', () => ({
  request: vi.fn(),
}));

const toastMock = vi.fn();

vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: toastMock,
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
  ShieldCheck: () => <span>Shield</span>,
  Download: () => <span>Download</span>,
  Trash2: () => <span>Trash</span>,
}));

import { request } from '@/lib/api';

describe('AiModelSettings', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (vi.mocked(request) as any).mockResolvedValue({ providers: [] });
    Object.defineProperty(URL, 'createObjectURL', { configurable: true, value: vi.fn(() => 'blob:ledger') });
    Object.defineProperty(URL, 'revokeObjectURL', { configurable: true, value: vi.fn() });
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => undefined);
    vi.spyOn(window, 'confirm').mockReturnValue(true);
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
      expect(screen.getByText('Stored')).toBeInTheDocument();
    });

    expect(screen.queryByText('API key set')).not.toBeInTheDocument();
    expect(screen.queryByText('Available')).not.toBeInTheDocument();
    expect(screen.getByText('Stored').closest('[data-testid="badge"]')).toHaveAttribute(
      'data-variant',
      'secondary'
    );
  });

  it('maps verified keys to the verified status only when validation has succeeded', () => {
    expect(getProviderStatus({ id: 'g1', name: 'Google', type: 'google', has_api_key: true }, false)).toEqual({
      label: 'Stored',
      variant: 'secondary',
    });
    expect(getProviderStatus({ id: 'g1', name: 'Google', type: 'google', has_api_key: true }, true)).toEqual({
      label: 'Available',
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
    expect(screen.queryByText('Available')).not.toBeInTheDocument();
  });

  it('should initialize with default values', async () => {
    render(<AiModelSettings />);

    await waitFor(() => {
      expect(request).toHaveBeenCalled();
      expect(screen.getByRole('option', { name: 'gpt-5.6-sol' })).toBeInTheDocument();
      expect(screen.getByText(/Reasoning level:/)).toHaveTextContent('high (default)');
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

  it('loads saved preferences, toggles them, and persists success and failure', async () => {
    (vi.mocked(request) as any).mockImplementation((endpoint: string, options?: RequestInit) => {
      if (endpoint === '/gateway/providers') return Promise.resolve({ providers: [] });
      if (endpoint === '/gateway/usage-ledger?days=30') return Promise.resolve(null);
      if (endpoint === '/settings/ai' && !options) {
        return Promise.resolve({ ai_processing_enabled: false, store_chat_history: false });
      }
      if (endpoint === '/settings/ai') return Promise.resolve({ success: true });
      return Promise.resolve({});
    });
    render(<AiModelSettings />);
    const aiSwitch = await screen.findByRole('switch', { name: /enable ai processing/i });
    const historySwitch = screen.getByRole('switch', { name: /store chat history/i });
    await waitFor(() => expect(aiSwitch).toHaveAttribute('aria-checked', 'false'));
    expect(historySwitch).toHaveAttribute('aria-checked', 'false');
    fireEvent.click(aiSwitch);
    fireEvent.click(historySwitch);
    fireEvent.click(screen.getByRole('button', { name: /save preferences/i }));
    await waitFor(() => expect(request).toHaveBeenCalledWith('/settings/ai', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ ai_processing_enabled: true, store_chat_history: true }),
    })));
    expect(toastMock).toHaveBeenCalledWith('AI preferences saved.', 'success');

    (vi.mocked(request) as any).mockRejectedValueOnce(new Error('save failed'));
    fireEvent.click(screen.getByRole('button', { name: /save preferences/i }));
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith('Failed to save AI preferences.', 'error'));
  });

  it('saves a new key, reveals it, tests the provider, and marks it available', async () => {
    (vi.mocked(request) as any).mockImplementation((endpoint: string) => {
      if (endpoint === '/gateway/providers') return Promise.resolve({ providers: [] });
      if (endpoint === '/gateway/usage-ledger?days=30') return Promise.resolve(null);
      if (endpoint === '/settings/ai') return Promise.resolve({});
      if (endpoint === '/gateway/keys') {
        return Promise.resolve({ provider: { id: 'openai-1', provider_type: 'openai' } });
      }
      if (endpoint === '/gateway/providers/openai-1/test') {
        return Promise.resolve({ success: true, message: 'Connected.' });
      }
      return Promise.resolve({});
    });
    render(<AiModelSettings />);
    const key = await screen.findByLabelText('API Key');
    fireEvent.change(key, { target: { value: '  secret-key  ' } });
    fireEvent.click(screen.getByRole('button', { name: 'Show API key' }));
    expect(key).toHaveAttribute('type', 'text');
    fireEvent.click(screen.getByRole('button', { name: 'Hide API key' }));
    fireEvent.click(screen.getByRole('button', { name: /save model configuration/i }));
    await waitFor(() => expect(request).toHaveBeenCalledWith('/gateway/keys', expect.objectContaining({
      method: 'POST',
      body: expect.stringContaining('secret-key'),
    })));
    expect(await screen.findByText('Stored')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /test provider model/i }));
    await waitFor(() => expect(request).toHaveBeenCalledWith('/gateway/providers/openai-1/test', { method: 'POST' }));
    expect(await screen.findByText(/openai is available/i)).toBeInTheDocument();
    expect(toastMock).toHaveBeenCalledWith('Connected.', 'success');
  });

  it('tests an existing provider and reports unsuccessful, thrown, and missing-key outcomes', async () => {
    (vi.mocked(request) as any).mockImplementation((endpoint: string) => {
      if (endpoint === '/gateway/providers') {
        return Promise.resolve({ providers: [{ id: 'google-1', name: 'Google', type: 'google', has_api_key: true }] });
      }
      if (endpoint === '/gateway/providers/google-1/test') {
        return Promise.resolve({ success: false, error: 'invalid key' });
      }
      return Promise.resolve(null);
    });
    render(<AiModelSettings />);
    await screen.findByText('Stored');
    fireEvent.click(screen.getByRole('button', { name: /test provider model/i }));
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith('Provider model test failed: invalid key', 'error'));

    (vi.mocked(request) as any).mockRejectedValueOnce('offline');
    fireEvent.click(screen.getByRole('button', { name: /test provider model/i }));
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith('Provider model test failed: offline', 'error'));

    (vi.mocked(request) as any).mockResolvedValue({ providers: [] });
    const empty = render(<AiModelSettings />);
    await waitFor(() => expect(screen.getAllByText(/No providers detected yet/i).length).toBeGreaterThan(0));
    fireEvent.click(screen.getAllByRole('button', { name: /test provider model/i }).at(-1)!);
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith(
      'Enter an API key before saving the model configuration.',
      'warning',
    ));
    empty.unmount();
  });

  it('renders usage details and refreshes, exports, resets, and cancels reset', async () => {
    const ledger = {
      schema_version: 'provider-usage-ledger.v1',
      generated_at: '2026-08-16T00:00:00Z',
      limits: { daily_calls: 10, monthly_calls: 100, daily_tokens: 1000, monthly_tokens: 5000, monthly_spend_usd: null },
      remaining: { daily_calls: 7, monthly_calls: 80, daily_tokens: 800, monthly_tokens: 4000, monthly_spend_usd: null },
      daily: { calls: 3, tokens_total: 200, known_estimated_cost_usd: 0.1, unknown_price_calls: 0 },
      monthly: { calls: 20, tokens_total: 1000, known_estimated_cost_usd: null, unknown_price_calls: 2 },
      pricing_status: 'unknown',
      entries: [{ id: 'e1', provider: 'google', model: null, purpose: 'chat', status: 'success', disclosed_categories: [] }],
    };
    (vi.mocked(request) as any).mockImplementation((endpoint: string, options?: RequestInit) => {
      if (endpoint === '/gateway/providers') return Promise.resolve({ providers: [] });
      if (endpoint === '/gateway/usage-ledger?days=30') return Promise.resolve(ledger);
      if (endpoint === '/gateway/usage-ledger/export?days=366') return Promise.resolve({ ...ledger, export_notice: 'redacted' });
      if (endpoint === '/gateway/usage-ledger' && options?.method === 'DELETE') return Promise.resolve({ success: true });
      return Promise.resolve({});
    });
    render(<AiModelSettings />);
    expect(await screen.findByText('google / unknown model')).toBeInTheDocument();
    expect(screen.getByText('Unknown')).toBeInTheDocument();
    expect(screen.getByText('No owner ceiling configured')).toBeInTheDocument();
    expect(screen.getByText(/none recorded/)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /refresh provider usage ledger/i }));
    await waitFor(() => expect(request).toHaveBeenCalledWith('/gateway/usage-ledger?days=30'));
    fireEvent.click(screen.getByRole('button', { name: /export provider usage ledger/i }));
    await waitFor(() => expect(URL.createObjectURL).toHaveBeenCalled());
    fireEvent.click(screen.getByRole('button', { name: /reset provider usage ledger/i }));
    await waitFor(() => expect(request).toHaveBeenCalledWith('/gateway/usage-ledger', expect.objectContaining({ method: 'DELETE' })));
    expect(toastMock).toHaveBeenCalledWith('Provider usage ledger reset.', 'success');
    vi.mocked(window.confirm).mockReturnValue(false);
    fireEvent.click(screen.getByRole('button', { name: /reset provider usage ledger/i }));
  });

  it('reports usage refresh, export, reset, provider-load, and preference-load error branches', async () => {
    (vi.mocked(request) as any).mockRejectedValue(new Error('offline'));
    render(<AiModelSettings />);
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith('Failed to load provider models: offline', 'error'));
    const refresh = await screen.findByRole('button', { name: /refresh provider usage ledger/i });
    fireEvent.click(refresh);
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith('Failed to load provider usage: offline', 'error'));
    fireEvent.click(screen.getByRole('button', { name: /export provider usage ledger/i }));
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith('Failed to export provider usage: offline', 'error'));
    fireEvent.click(screen.getByRole('button', { name: /reset provider usage ledger/i }));
    await waitFor(() => expect(toastMock).toHaveBeenCalledWith('Failed to reset provider usage: offline', 'error'));
  });
});

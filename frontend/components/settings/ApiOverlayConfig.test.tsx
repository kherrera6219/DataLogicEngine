import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ApiOverlayConfig } from './ApiOverlayConfig';

const toastMock = vi.fn();

// Mock UI components
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: toastMock })
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({ children, value, onChange, ...props }: { children: React.ReactNode; value: string; onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void } & React.SelectHTMLAttributes<HTMLSelectElement>) => (
    <select value={value} onChange={onChange} data-testid="select" title="API Provider Selection" {...props}>
      {children}
    </select>
  )
}));

vi.mock('recharts', () => ({
  ResponsiveContainer: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  BarChart: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  Bar: () => null,
  XAxis: () => null,
  Tooltip: () => null,
  Cell: () => null
}));

vi.mock('lucide-react', () => ({
  BarChart3: () => <div data-testid="bar-chart-icon" />,
  Terminal: () => <div data-testid="terminal-icon" />,
  Play: () => <div data-testid="play-icon" />,
  Copy: () => <div data-testid="copy-icon" />,
  RefreshCw: () => <div data-testid="refresh-cw-icon" />,
  Eye: () => <div data-testid="eye-icon" />,
  CheckCircle: () => <div data-testid="check-circle-icon" />,
  Shield: () => <div data-testid="shield-icon" />,
  ArrowRight: () => <div data-testid="arrow-right-icon" />,
  Server: () => <div data-testid="server-icon" />,
  Activity: () => <div data-testid="activity-icon" />,
  Lock: () => <div data-testid="lock-icon" />,
}));

function jsonResponse(body: unknown, status = 200) {
  return {
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: { get: () => 'application/json' },
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

beforeEach(() => {
  toastMock.mockReset();
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);

    if (url.includes('/gateway/providers/provider-openai-id/test')) {
      return jsonResponse({ success: true, message: 'Provider connection successful' });
    }
    if (url.includes('/gateway/keys')) {
      return jsonResponse({
        success: true,
        provider: {
          id: 'provider-openai-id',
          provider_type: 'openai',
          name: 'Openai',
        },
      });
    }
    if (url.includes('/gateway/providers')) {
      return jsonResponse({
        providers: [{
          id: 'provider-openai-id',
          name: 'OpenAI',
          type: 'openai',
          model: 'gpt-5.5',
          is_default: true,
        }]
      });
    }
    if (url.includes('/analytics/activity')) {
      return jsonResponse([]);
    }
    if (url.includes('/gateway/health')) {
      return jsonResponse({ active_providers: 1, message: 'Gateway operational' });
    }
    if (url.includes('/analytics/overview')) {
      return jsonResponse({ compliance_score: 99.5 });
    }
    if (url.includes('/gateway/chat')) {
      return jsonResponse({ response: 'Gateway response body', run_id: 'run-1' });
    }

    return jsonResponse({ success: true });
  }));
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('ApiOverlayConfig', () => {
  it('should render configuration header', () => {
    render(<ApiOverlayConfig />);
    expect(screen.getByText('UKG API Overlay Configuration')).toBeInTheDocument();
    expect(screen.getByText('Valid')).toBeInTheDocument();
  });

  it('should allow entering API key', () => {
    render(<ApiOverlayConfig />);
    const input = screen.getByLabelText('API Key');
    fireEvent.change(input, { target: { value: 'sk-test-123' } });
    expect(input).toHaveValue('sk-test-123');
  });

  it('should save provider key explicitly', async () => {
    render(<ApiOverlayConfig />);
    const input = screen.getByLabelText('API Key');
    fireEvent.change(input, { target: { value: 'sk-test-123' } });

    const saveBtn = screen.getByRole('button', { name: 'Save provider key' });
    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(screen.getAllByText('Saved')).toHaveLength(2);
    }, { timeout: 2000 });
  });

  it('should test provider connection', async () => {
    render(<ApiOverlayConfig />);
    const input = screen.getByLabelText('API Key');
    fireEvent.change(input, { target: { value: 'sk-test-123' } });

    const testBtn = screen.getByRole('button', { name: 'Test provider connection' });
    fireEvent.click(testBtn);

    await waitFor(() => {
      expect(screen.getByText('Connected')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('surfaces the provider-test HTTP status code inline on failure (C3)', async () => {
    // Re-stub fetch so the provider-test endpoint returns a 401, while the
    // provider list / save endpoints still succeed.
    vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes('/gateway/providers/provider-openai-id/test')) {
        return jsonResponse({ error: 'authentication failed' }, 401);
      }
      if (url.includes('/gateway/keys')) {
        return jsonResponse({
          success: true,
          provider: { id: 'provider-openai-id', provider_type: 'openai', name: 'Openai' },
        });
      }
      if (url.includes('/gateway/providers')) {
        return jsonResponse({
          providers: [{ id: 'provider-openai-id', name: 'OpenAI', type: 'openai', model: 'gpt-5.5', is_default: true }],
        });
      }
      if (url.includes('/analytics/activity')) return jsonResponse([]);
      if (url.includes('/gateway/health')) return jsonResponse({ active_providers: 1 });
      if (url.includes('/analytics/overview')) return jsonResponse({ compliance_score: 99.5 });
      return jsonResponse({ success: true });
    }));

    render(<ApiOverlayConfig />);
    const input = screen.getByLabelText('API Key');
    fireEvent.change(input, { target: { value: 'sk-bad-key' } });

    fireEvent.click(screen.getByRole('button', { name: 'Test provider connection' }));

    await waitFor(() => {
      expect(screen.getByText('Connection Error')).toBeInTheDocument();
      expect(screen.getByText('HTTP 401')).toBeInTheDocument();
      expect(screen.getByText(/Invalid API key/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should run playground test', async () => {
    render(<ApiOverlayConfig />);
    const promptInput = screen.getByLabelText('Test Prompt');
    fireEvent.change(promptInput, { target: { value: 'Test query' } });

    const runBtn = screen.getByRole('button', { name: 'Run enhancement test' });
    fireEvent.click(runBtn);

    await waitFor(() => {
      expect(screen.getByText(/Gateway response body/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('should expose labeled provider controls and tier buttons', async () => {
    render(<ApiOverlayConfig />);

    expect(screen.getByRole('combobox', { name: 'Provider' })).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: 'Model' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Processing tier Trivial' })).toBeInTheDocument();
    expect(screen.getByRole('slider', { name: 'Confidence threshold' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Copy gateway endpoint' })).toBeInTheDocument();
  });
});

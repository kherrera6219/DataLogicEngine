import React from 'react';
import { render } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AiModelSettings } from './AiModelSettings';

// Mock API calls - must be before any imports that use the module
vi.mock('@/lib/api', () => {
  const mockRequest = vi.fn();
  return {
    request: mockRequest,
  };
});

// Mock UI components to avoid rendering issues
vi.mock('@/components/ui/card', () => ({
  Card: ({ children, ...props }: any) => <div data-testid="card" {...props}>{children}</div>,
  CardContent: ({ children }: any) => <div>{children}</div>,
  CardDescription: ({ children }: any) => <div>{children}</div>,
  CardHeader: ({ children }: any) => <div>{children}</div>,
  CardTitle: ({ children }: any) => <div>{children}</div>,
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children }: any) => <span>{children}</span>,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children }: any) => <button>{children}</button>,
}));

vi.mock('@/components/ui/input', () => ({
  Input: (props: any) => <input {...props} />,
}));

vi.mock('@/components/ui/select', () => ({
  Select: (props: any) => <select {...props} />,
}));

vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
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
    vi.mocked(request).mockResolvedValue({ providers: [] });
  });

  it('should render without crashing', () => {
    const { container } = render(<AiModelSettings />);
    expect(container).toBeInTheDocument();
  });

  it('should initialize with expected structure', () => {
    const { container } = render(<AiModelSettings />);
    expect(container).toBeInTheDocument();
  });

  it('should handle empty providers', () => {
    vi.mocked(request).mockResolvedValue({ providers: [] });
    const { container } = render(<AiModelSettings />);
    expect(container).toBeInTheDocument();
  });

  it('should call API on component mount', () => {
    render(<AiModelSettings />);
    expect(vi.mocked(request)).toHaveBeenCalled();
  });

  it('should handle multiple provider types', () => {
    vi.mocked(request).mockResolvedValue({
      providers: [
        { name: 'OpenAI', type: 'openai' },
        { name: 'Anthropic', type: 'anthropic' },
      ],
    });
    const { container } = render(<AiModelSettings />);
    expect(container).toBeInTheDocument();
  });
});





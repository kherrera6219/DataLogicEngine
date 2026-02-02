import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ApiOverlayConfig } from './ApiOverlayConfig';

// Mock UI components
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({ toast: vi.fn() })
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardHeader: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardTitle: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  CardContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>
}));

vi.mock('@/components/ui/select', () => ({
  Select: ({ children, value, onChange }: any) => (
    <select value={value} onChange={onChange} data-testid="select">
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

describe('ApiOverlayConfig', () => {
  it('should render configuration header', () => {
    render(<ApiOverlayConfig />);
    expect(screen.getByText('UKG API Overlay Configuration')).toBeInTheDocument();
    expect(screen.getByText('Valid')).toBeInTheDocument();
  });

  it('should allow entering API key', () => {
    render(<ApiOverlayConfig />);
    const inputs = screen.getAllByPlaceholderText('sk-...');
    fireEvent.change(inputs[0], { target: { value: 'sk-test-123' } });
    expect(inputs[0]).toHaveValue('sk-test-123');
  });

  it('should handle connection test', async () => {
    render(<ApiOverlayConfig />);
    const inputs = screen.getAllByPlaceholderText('sk-...');
    fireEvent.change(inputs[0], { target: { value: 'sk-test-123' } });
    
    // Find button that says 'Test' (or 'Connected' if state changes)
    const testBtn = screen.getByText('Test');
    fireEvent.click(testBtn);
    
    expect(screen.getByText('Testing...')).toBeInTheDocument();
    
    await waitFor(() => {
        expect(screen.getByText('Connected')).toBeInTheDocument();
    }, { timeout: 2000 });
  });

  it('should run playground test', async () => {
    render(<ApiOverlayConfig />);
    const promptInput = screen.getByLabelText('Test Prompt');
    fireEvent.change(promptInput, { target: { value: 'Test query' } });
    
    const runBtn = screen.getByText('Test Enhancement');
    fireEvent.click(runBtn);
    
    // Check loading state
    expect(screen.getByTestId('refresh-cw-icon')).toBeInTheDocument; // implied since spinner is rendered
    
    await waitFor(() => {
        expect(screen.getByText(/The proposed architecture/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});

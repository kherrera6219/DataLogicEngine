import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, it, expect, vi } from 'vitest';
import { CommandBar } from './CommandBar';

const mockPush = vi.fn();
let mockPathname = '/dashboard';

vi.mock('next/navigation', () => ({
  usePathname: vi.fn(() => mockPathname),
  useRouter: vi.fn(() => ({ push: mockPush }))
}));

vi.mock('@/components/ui/breadcrumbs', () => ({
  Breadcrumbs: ({ items }: { items: Array<{ label: string }> }) => <div>{items.map((i) => i.label).join(' > ')}</div>
}));

// Mock Lucide icons to avoid "render children" issues if any
vi.mock('lucide-react', () => ({
  Search: () => <svg data-testid="icon-search" />,
  Settings: () => <svg data-testid="icon-settings" />,
  LayoutGrid: () => <svg data-testid="icon-grid" />,
  Download: () => <svg data-testid="icon-download" />,
  HelpCircle: () => <svg data-testid="icon-help" />
}));

describe('CommandBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPathname = '/dashboard';
  });

  it('should render brand and breadcrumbs', () => {
    render(<CommandBar />);
    expect(screen.getByText('DataLogic')).toBeInTheDocument();
    expect(screen.getByText('Engine')).toBeInTheDocument();
    expect(screen.getByText('Executive Dashboard')).toBeInTheDocument();
  });

  it('should render search input', () => {
    render(<CommandBar />);
    expect(screen.getByRole('textbox', { name: /global search/i })).toBeInTheDocument();
  });

  it('should render action buttons', () => {
    render(<CommandBar />);
    expect(screen.getByLabelText('Help and Documentation')).toBeInTheDocument();
    expect(screen.getByLabelText('Open export history')).toBeInTheDocument();
    expect(screen.getByLabelText('Account and System Settings')).toBeInTheDocument();
  });

  it('focuses the search input with Alt+K', () => {
    render(<CommandBar />);
    const input = screen.getByRole('textbox', { name: /global search/i });

    fireEvent.keyDown(window, { key: 'k', altKey: true });

    expect(input).toHaveFocus();
    expect(input).toHaveAttribute('aria-keyshortcuts', 'Alt+K');
  });

  it('submits the query to the graph search route', () => {
    render(<CommandBar />);
    const input = screen.getByRole('textbox', { name: /global search/i });

    fireEvent.change(input, { target: { value: 'risk register' } });
    fireEvent.submit(input.closest('form')!);

    expect(mockPush).toHaveBeenCalledWith('/graph?search=risk%20register');
  });

  it('routes empty searches to the graph landing page', () => {
    render(<CommandBar />);
    const input = screen.getByRole('textbox', { name: /global search/i });

    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.submit(input.closest('form')!);

    expect(mockPush).toHaveBeenCalledWith('/graph');
  });

  it('renders graph and chat breadcrumbs for those routes', () => {
    mockPathname = '/graph';
    const { rerender } = render(<CommandBar />);
    expect(screen.getByText('Knowledge Graph Explorer')).toBeInTheDocument();

    mockPathname = '/chat';
    rerender(<CommandBar />);
    expect(screen.getByText('Intelligence Interface')).toBeInTheDocument();
  });

  it('omits breadcrumbs for unknown routes', () => {
    mockPathname = '/unknown';
    render(<CommandBar />);
    expect(screen.queryByText('Executive Dashboard')).not.toBeInTheDocument();
    expect(screen.queryByText('Knowledge Graph Explorer')).not.toBeInTheDocument();
    expect(screen.queryByText('Intelligence Interface')).not.toBeInTheDocument();
  });

  it('navigates from launcher and action buttons', () => {
    render(<CommandBar />);

    fireEvent.click(screen.getByRole('button', { name: /open application launcher/i }));
    fireEvent.click(screen.getByRole('button', { name: /help and documentation/i }));
    fireEvent.click(screen.getByRole('button', { name: /open export history/i }));
    fireEvent.click(screen.getByRole('button', { name: /account and system settings/i }));
    fireEvent.click(screen.getByRole('button', { name: /user profile: admin user/i }));

    expect(mockPush).toHaveBeenCalledWith('/dashboard');
    expect(mockPush).toHaveBeenCalledWith('/about');
    expect(mockPush).toHaveBeenCalledWith('/tools/history');
    expect(mockPush).toHaveBeenCalledWith('/settings');
    expect(mockPush).toHaveBeenCalledWith('/profile');
  });
});

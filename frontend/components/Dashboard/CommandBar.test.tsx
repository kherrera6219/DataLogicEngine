import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { CommandBar } from './CommandBar';

// Mock mocks
vi.mock('next/navigation', () => ({
  usePathname: vi.fn(() => '/dashboard')
}));

vi.mock('@/components/ui/breadcrumbs', () => ({
  Breadcrumbs: ({ items }) => <div>{items.map(i => i.label).join(' > ')}</div>
}));

// Mock Lucide icons to avoid "render children" issues if any
vi.mock('lucide-react', () => ({
  Search: () => <svg data-testid="icon-search" />,
  Settings: () => <svg data-testid="icon-settings" />,
  Bell: () => <svg data-testid="icon-bell" />,
  LayoutGrid: () => <svg data-testid="icon-grid" />,
  Download: () => <svg data-testid="icon-download" />,
  HelpCircle: () => <svg data-testid="icon-help" />
}));

describe('CommandBar', () => {
  it('should render brand and breadcrumbs', () => {
    render(<CommandBar />);
    expect(screen.getByText('DataLogic')).toBeInTheDocument();
    expect(screen.getByText('Engine')).toBeInTheDocument();
    expect(screen.getByText('Executive Dashboard')).toBeInTheDocument();
  });

  it('should render search input', () => {
    render(<CommandBar />);
    expect(screen.getByPlaceholderText(/search nodes/i)).toBeInTheDocument();
  });

  it('should render action buttons', () => {
    render(<CommandBar />);
    expect(screen.getByLabelText('Help and Documentation')).toBeInTheDocument();
    expect(screen.getByLabelText('View Notifications')).toBeInTheDocument();
  });
});

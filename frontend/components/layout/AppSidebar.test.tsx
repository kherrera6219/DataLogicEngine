import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AppSidebar } from './AppSidebar';
import { useAuth } from '@/contexts/AuthContext';

// Mock routing
vi.mock('next/navigation', () => ({
  usePathname: vi.fn(() => '/dashboard')
}));

vi.mock('next/link', () => ({
  default: ({ children, href, ...props }: any) => <a href={href} {...props}>{children}</a>,
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

// Mock icons
vi.mock('lucide-react', () => ({
  LayoutDashboard: () => <svg data-testid="icon-dashboard" />,
  MessageSquare: () => <svg data-testid="icon-chat" />,
  Database: () => <svg data-testid="icon-db" />,
  Folder: () => <svg data-testid="icon-folder" />,
  FlaskConical: () => <svg data-testid="icon-simulations" />,
  BookOpen: () => <svg data-testid="icon-knowledge" />,
  Share2: () => <svg data-testid="icon-graph" />,
  Binary: () => <svg data-testid="icon-algorithms" />,
  ScrollText: () => <svg data-testid="icon-runs" />,
  ShieldCheck: () => <svg data-testid="icon-truth" />,
  BarChart3: () => <svg data-testid="icon-analytics" />,
  ClipboardCheck: () => <svg data-testid="icon-compliance" />,
  Activity: () => <svg data-testid="icon-diagnostics" />,
  ShieldAlert: () => <svg data-testid="icon-shield" />,
  Settings: () => <svg data-testid="icon-settings" />,
  Hexagon: () => <svg data-testid="icon-hexagon" />,
  PanelLeftClose: () => <svg data-testid="icon-panel-close" />,
  PanelLeftOpen: () => <svg data-testid="icon-panel-open" />,
}));

describe('AppSidebar', () => {
  const mockLogout = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    (useAuth as any).mockReturnValue({
      user: {
        username: 'Test User',
        role: 'admin',
        is_admin: true,
      },
      logout: mockLogout,
    });
  });

  it('should render sidebar items', () => {
    render(<AppSidebar />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Enterprise AI')).toBeInTheDocument();
    expect(screen.getByText('Diagnostics')).toBeInTheDocument();
  });

  it('shows Algorithms in the System group for an admin', () => {
    render(<AppSidebar />);
    expect(screen.getByText('Algorithms')).toBeInTheDocument();
  });

  it('hides Algorithms from a non-admin', () => {
    // The page can create, confirm, and execute durable plans that produce
    // effect proposals, so it is gated with the other operator surfaces
    // rather than sitting beside read-only Knowledge pages.
    (useAuth as any).mockReturnValue({
      user: { username: 'Standard User', role: 'user', is_admin: false },
      logout: mockLogout,
    });
    render(<AppSidebar />);
    expect(screen.queryByText('Algorithms')).not.toBeInTheDocument();
    expect(screen.queryByText('Diagnostics')).not.toBeInTheDocument();
    expect(screen.getByText('Knowledge Base')).toBeInTheDocument();
  });

  it('should highlight active route', () => {
    render(<AppSidebar />);
    // "Dashboard" should be active based on mock pathname
    const dashboardLink = screen.getByRole('link', { name: 'Dashboard' });
    expect(dashboardLink.firstElementChild).toHaveClass('bg-white/5');
  });

  it('should toggle collapse', () => {
    render(<AppSidebar />);
    const toggle = screen.getByRole('button', { name: /collapse sidebar/i });
    fireEvent.click(toggle);

    expect(screen.queryByText(/UKG/i)).not.toBeInTheDocument();
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /expand sidebar/i })).toBeInTheDocument();
  });
});

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
  ShieldAlert: () => <svg data-testid="icon-shield" />,
  Settings: () => <svg data-testid="icon-settings" />,
  LogOut: () => <svg data-testid="icon-logout" />,
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

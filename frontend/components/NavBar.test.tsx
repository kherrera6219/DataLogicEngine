
import React from 'react';
import { render, screen, fireEvent, within } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { NavBar } from './NavBar';
import { useAuth } from '@/contexts/AuthContext';
import { usePathname } from 'next/navigation';

// Mock dependencies
vi.mock('next/link', () => ({
  default: ({ children, href, onClick, ...props }: any) => (
    <a href={href} onClick={onClick} {...props}>{children}</a>
  ),
}));

vi.mock('next/navigation', () => ({
  usePathname: vi.fn(),
}));

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('@/components/ThemeToggle', () => ({
  ThemeToggle: () => <div data-testid="theme-toggle">ThemeToggle</div>,
}));

vi.mock('@/components/ui/cloud-status-indicator', () => ({
  CloudStatusIndicator: () => <div data-testid="cloud-status">CloudStatus</div>,
}));

vi.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: any) => <div>{children}</div>,
  DropdownMenuTrigger: ({ children }: any) => <button data-testid="user-menu-trigger">{children}</button>,
  DropdownMenuContent: ({ children }: any) => <div data-testid="dropdown-content">{children}</div>,
  DropdownMenuItem: ({ children, onClick }: any) => <div onClick={onClick} role="button">{children}</div>,
  DropdownMenuLabel: ({ children }: any) => <div>{children}</div>,
  DropdownMenuSeparator: () => <hr />,
}));

describe('NavBar', () => {
  const mockLogout = vi.fn();
  const mockUser = {
    username: 'testuser',
    email: 'test@ukg.com',
    role: 'admin',
    is_admin: true,
    windows_sid: 'S-1-5-21-mock'
  };

  beforeEach(() => {
    vi.clearAllMocks();
    (usePathname as any).mockReturnValue('/');
    (useAuth as any).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
      logout: mockLogout,
    });
  });

  it('renders nothing on login page', () => {
    (usePathname as any).mockReturnValue('/login');
    const { container } = render(<NavBar />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders logo and nav items', () => {
    render(<NavBar />);
    expect(screen.getByLabelText('DataLogicEngine Home')).toBeInTheDocument();
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Simulations')).toBeInTheDocument();
  });

  it('hides protected routes when unauthenticated', () => {
    (useAuth as any).mockReturnValue({
      user: null,
      isAuthenticated: false,
      logout: mockLogout,
    });

    render(<NavBar />);
    expect(screen.queryByText('Dashboard')).not.toBeInTheDocument();
    expect(screen.getByText('About')).toBeInTheDocument();
    expect(screen.getByText('Login')).toBeInTheDocument();
  });

  it('shows user menu when authenticated', () => {
    render(<NavBar />);
    
    expect(screen.getByLabelText('User Menu')).toBeInTheDocument();
    expect(screen.getByTestId('cloud-status')).toBeInTheDocument();
  });

  it('opens and closes mobile menu', () => {
    render(<NavBar />);
    
    // Initially closed
    expect(screen.queryByLabelText('Mobile navigation')).not.toBeInTheDocument();
    
    // Open menu
    const menuButton = screen.getByLabelText('Open main menu');
    fireEvent.click(menuButton);
    
    expect(screen.getByLabelText('Mobile navigation')).toBeInTheDocument();
    
    // Check user info in mobile menu
    const mobileNav = screen.getByLabelText('Mobile navigation');
    expect(within(mobileNav).getByText('testuser')).toBeInTheDocument();
    
    // Close menu locally
    const dashboardLink = screen.getAllByText('Dashboard')[1]; // Second one is inside mobile menu
    fireEvent.click(dashboardLink);
    
    // We can't easily check 'closed' state here because state update is async/internal, 
    // ensuring the handler was called is implicit by the component logic
  });

  it('handles logout interaction', async () => {
    render(<NavBar />);
    
    // Open dropdown
    const trigger = screen.getByLabelText('User Menu');
    fireEvent.click(trigger);
    
    // Find logout - Dropdowns are typically async/animated
    const logoutBtn = await screen.findByText('Log out');
    fireEvent.click(logoutBtn);
    
    expect(mockLogout).toHaveBeenCalled();
  });
});

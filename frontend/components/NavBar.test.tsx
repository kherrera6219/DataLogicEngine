
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
  DropdownMenuTrigger: ({ children, asChild }: any) =>
    asChild && React.isValidElement(children)
      ? React.cloneElement(children, { 'data-testid': 'user-menu-trigger' } as React.HTMLAttributes<HTMLElement>)
      : <button data-testid="user-menu-trigger">{children}</button>,
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

  it('renders logo and global chrome (primary nav lives in AppSidebar)', () => {
    render(<NavBar />);
    expect(screen.getByLabelText('DataLogicEngine Home')).toBeInTheDocument();
    expect(screen.getByTestId('cloud-status')).toBeInTheDocument();
    expect(screen.getByTestId('theme-toggle')).toBeInTheDocument();
    // NavBar no longer duplicates primary page links — those moved to AppSidebar.
    expect(screen.queryByText('Simulations')).not.toBeInTheDocument();
  });

  it('shows only chrome (no user menu) when unauthenticated', () => {
    (useAuth as any).mockReturnValue({
      user: null,
      isAuthenticated: false,
      logout: mockLogout,
    });

    render(<NavBar />);
    expect(screen.getByLabelText('DataLogicEngine Home')).toBeInTheDocument();
    expect(screen.queryByLabelText('User Menu')).not.toBeInTheDocument();
  });

  it('shows user menu when authenticated', () => {
    render(<NavBar />);
    
    expect(screen.getByLabelText('User Menu')).toBeInTheDocument();
    expect(screen.getByTestId('cloud-status')).toBeInTheDocument();
  });

  it('opens and closes mobile account menu', () => {
    render(<NavBar />);

    // Initially closed
    expect(screen.queryByLabelText('Mobile account menu')).not.toBeInTheDocument();

    // Open menu
    const menuButton = screen.getByLabelText('Open main menu');
    fireEvent.click(menuButton);

    expect(screen.getByLabelText('Mobile account menu')).toBeInTheDocument();

    // Check user info in mobile menu
    const mobileNav = screen.getByLabelText('Mobile account menu');
    expect(within(mobileNav).getByText('testuser')).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText('Close main menu'));
    expect(screen.queryByLabelText('Mobile account menu')).not.toBeInTheDocument();
  });

  it('does not expose logout controls in desktop local-first mode', async () => {
    render(<NavBar />);
    
    // Open dropdown
    const trigger = screen.getByLabelText('User Menu');
    fireEvent.click(trigger);
    
    expect(screen.queryByText('Log out')).not.toBeInTheDocument();
    expect(mockLogout).not.toHaveBeenCalled();
  });
});

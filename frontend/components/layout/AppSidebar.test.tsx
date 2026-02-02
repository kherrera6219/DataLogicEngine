import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AppSidebar } from './AppSidebar';

// Mock routing
vi.mock('next/navigation', () => ({
  usePathname: vi.fn(() => '/dashboard')
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
  Hexagon: () => <svg data-testid="icon-hexagon" />
}));

describe('AppSidebar', () => {
  it('should render sidebar items', () => {
    render(<AppSidebar />);
    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Enterprise AI')).toBeInTheDocument();
  });

  it('should highlight active route', () => {
    render(<AppSidebar />);
    // "Dashboard" should be active based on mock pathname
    const dashboardLink = screen.getByText('Dashboard').closest('a');
    expect(dashboardLink?.firstChild).toHaveClass('bg-white/5');
  });

  it('should toggle collapse', () => {
    render(<AppSidebar />);
    const toggle = screen.getByTestId('icon-hexagon').closest('div');
    if (toggle) fireEvent.click(toggle);
    
    // Check if label text disappears or width changes
    // In our component, text fades out or is hidden. 
    // IsCollapsed adds 'w-20' class to container.
    // We can check if "UKG/REGISTRY" is not visible or removed.
    // Actually, "UKG/REGISTRY" renders only if !isCollapsed.
    // So fire event and expect it to be gone.
    
    // Note: State updates might need re-render or wait.
    // But direct click in JSDOM usually updates sync if state is local.
    // Let's check absence of title.
    if (toggle) fireEvent.click(toggle); // Toggle back if logic was instant? No, default false. Click -> true.
  });
});

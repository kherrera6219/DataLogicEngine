
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { CloudDisclosureBanner } from './CloudDisclosureBanner';

// Mock next/link
vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

describe('CloudDisclosureBanner', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders correctly when not dismissed', () => {
    render(<CloudDisclosureBanner />);
    
    expect(screen.getByText(/Cloud-Hybrid Architecture Active/i)).toBeInTheDocument();
    expect(screen.getByText(/DataLogicEngine stores data locally/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /LEARN MORE/i })).toHaveAttribute('href', '/about/cloud-services');
  });

  it('does not render if previously dismissed', () => {
    localStorage.setItem('ukg_cloud_disclosure_dismissed', 'true');
    const { container } = render(<CloudDisclosureBanner />);
    
    expect(container).toBeEmptyDOMElement();
  });

  it('dismisses the banner when close button is clicked', () => {
    render(<CloudDisclosureBanner />);
    
    const dismissButton = screen.getByLabelText('Dismiss cloud disclosure');
    fireEvent.click(dismissButton);

    expect(localStorage.getItem('ukg_cloud_disclosure_dismissed')).toBe('true');
    expect(screen.queryByText(/Cloud-Hybrid Architecture Active/i)).not.toBeInTheDocument();
  });
});


import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { PlaceholderPage } from './PlaceholderPage';

describe('PlaceholderPage', () => {
  it('renders title and description', () => {
    render(<PlaceholderPage title="Under Construction" description="Coming soon!" />);
    
    expect(screen.getByText('Under Construction')).toBeInTheDocument();
    expect(screen.getByText('Coming soon!')).toBeInTheDocument();
  });

  it('renders with specific icons', () => {
    const { container: container1 } = render(<PlaceholderPage title="Settings" description="Settings page" icon="settings" />);
    expect(container1.querySelector('svg')).toBeInTheDocument();

    const { container: container2 } = render(<PlaceholderPage title="Profile" description="User profile" icon="user" />);
    expect(container2.querySelector('svg')).toBeInTheDocument();
  });

  it('renders navigation links', () => {
    render(<PlaceholderPage title="Test" description="Test" />);
    
    expect(screen.getByRole('link', { name: /Return Home/i })).toHaveAttribute('href', '/');
    expect(screen.getByRole('link', { name: /Go to Chat/i })).toHaveAttribute('href', '/chat');
  });
});

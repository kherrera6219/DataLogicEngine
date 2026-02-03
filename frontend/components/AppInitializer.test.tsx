
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { AppInitializer } from './AppInitializer';

// Mock the AuthContext
const mockUseAuth = vi.fn();
vi.mock('@/contexts/AuthContext', () => ({
  useAuth: () => mockUseAuth(),
}));

describe('AppInitializer', () => {
  it('shows loading spinner when isLoading is true', () => {
    mockUseAuth.mockReturnValue({ isLoading: true });
    
    render(
      <AppInitializer>
        <div data-testid="child-content">Child Content</div>
      </AppInitializer>
    );

    expect(screen.getByText('Initializing DataLogicEngine...')).toBeInTheDocument();
    expect(screen.queryByTestId('child-content')).not.toBeInTheDocument();
  });

  it('renders children when isLoading is false', () => {
    mockUseAuth.mockReturnValue({ isLoading: false });
    
    render(
      <AppInitializer>
        <div data-testid="child-content">Child Content</div>
      </AppInitializer>
    );

    expect(screen.queryByText('Initializing DataLogicEngine...')).not.toBeInTheDocument();
    expect(screen.getByTestId('child-content')).toBeInTheDocument();
  });
});

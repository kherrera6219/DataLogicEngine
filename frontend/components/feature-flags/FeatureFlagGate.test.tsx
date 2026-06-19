import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FeatureFlagGate } from './FeatureFlagGate';
import { useFeatureFlags } from '@/contexts/FeatureFlagContext';

// Mock the feature flags context
vi.mock('@/contexts/FeatureFlagContext', () => ({
  useFeatureFlags: vi.fn(),
}));

describe('FeatureFlagGate', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render children when flag is enabled', () => {
    vi.mocked(useFeatureFlags).mockReturnValue({
      isEnabled: (flag: string) => flag === 'test-flag',
    } as any);

    render(
      <FeatureFlagGate flag="test-flag">
        <div>Feature content</div>
      </FeatureFlagGate>
    );

    expect(screen.getByText('Feature content')).toBeInTheDocument();
  });

  it('should render fallback when flag is disabled', () => {
    vi.mocked(useFeatureFlags).mockReturnValue({
      isEnabled: () => false,
    } as any);

    render(
      <FeatureFlagGate flag="disabled-flag" fallback={<div>Fallback content</div>}>
        <div>Feature content</div>
      </FeatureFlagGate>
    );

    expect(screen.getByText('Fallback content')).toBeInTheDocument();
    expect(screen.queryByText('Feature content')).not.toBeInTheDocument();
  });

  it('should render nothing when flag is disabled and no fallback', () => {
    vi.mocked(useFeatureFlags).mockReturnValue({
      isEnabled: () => false,
    } as any);

    const { container } = render(
      <FeatureFlagGate flag="disabled-flag">
        <div>Feature content</div>
      </FeatureFlagGate>
    );

    expect(screen.queryByText('Feature content')).not.toBeInTheDocument();
    expect(container.innerHTML).toBe('');
  });

  it('should call isEnabled with correct flag name', () => {
    const mockIsEnabled = vi.fn(() => true);
    vi.mocked(useFeatureFlags).mockReturnValue({
      isEnabled: mockIsEnabled,
    } as any);

    render(
      <FeatureFlagGate flag="custom-flag">
        <div>Content</div>
      </FeatureFlagGate>
    );

    expect(mockIsEnabled).toHaveBeenCalledWith('custom-flag');
  });

  it('should render complex children correctly', () => {
    vi.mocked(useFeatureFlags).mockReturnValue({
      isEnabled: () => true,
    } as any);

    render(
      <FeatureFlagGate flag="test-flag">
        <section>
          <h2>Feature Title</h2>
          <p>Description</p>
          <button>Action</button>
        </section>
      </FeatureFlagGate>
    );

    expect(screen.getByText('Feature Title')).toBeInTheDocument();
    expect(screen.getByText('Description')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Action' })).toBeInTheDocument();
  });

  it('should handle multiple different flags', () => {
    const mockIsEnabled = vi.fn((flag: string) => flag === 'enabled-flag');
    vi.mocked(useFeatureFlags).mockReturnValue({
      isEnabled: mockIsEnabled,
    } as any);

    const { rerender } = render(
      <FeatureFlagGate flag="enabled-flag">
        <div>Enabled</div>
      </FeatureFlagGate>
    );

    expect(screen.getByText('Enabled')).toBeInTheDocument();

    rerender(
      <FeatureFlagGate flag="disabled-flag">
        <div>Disabled</div>
      </FeatureFlagGate>
    );

    expect(screen.queryByText('Disabled')).not.toBeInTheDocument();
  });
});

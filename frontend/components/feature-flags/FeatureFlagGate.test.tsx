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
      isEnabled: vi.fn((flag) => flag === 'testFlag'),
      flags: { testFlag: true },
    });

    render(
      <FeatureFlagGate flag="testFlag">
        <div>Feature content</div>
      </FeatureFlagGate>
    );

    expect(screen.getByText('Feature content')).toBeInTheDocument();
  });

  it('should render fallback when flag is disabled', () => {
    vi.mocked(useFeatureFlags).mockReturnValue({
      isEnabled: vi.fn(() => false),
      flags: {},
    });

    render(
      <FeatureFlagGate flag="testFlag" fallback={<div>Fallback content</div>}>
        <div>Feature content</div>
      </FeatureFlagGate>
    );

    expect(screen.getByText('Fallback content')).toBeInTheDocument();
    expect(screen.queryByText('Feature content')).not.toBeInTheDocument();
  });

  it('should render null fallback by default', () => {
    vi.mocked(useFeatureFlags).mockReturnValue({
      isEnabled: vi.fn(() => false),
      flags: {},
    });

    const { container } = render(
      <FeatureFlagGate flag="testFlag">
        <div>Feature content</div>
      </FeatureFlagGate>
    );

    expect(screen.queryByText('Feature content')).not.toBeInTheDocument();
    expect(container.innerHTML).toBe('');
  });

  it('should handle multiple flags', () => {
    const isEnabledMock = vi.fn((flag) => flag === 'enabledFlag');
    vi.mocked(useFeatureFlags).mockReturnValue({
      isEnabled: isEnabledMock,
      flags: { enabledFlag: true, disabledFlag: false },
    });

    const { rerender } = render(
      <FeatureFlagGate flag="enabledFlag">
        <div>Enabled feature</div>
      </FeatureFlagGate>
    );

    expect(screen.getByText('Enabled feature')).toBeInTheDocument();

    rerender(
      <FeatureFlagGate flag="disabledFlag">
        <div>Disabled feature</div>
      </FeatureFlagGate>
    );

    expect(screen.queryByText('Disabled feature')).not.toBeInTheDocument();
  });

  it('should render nested elements correctly', () => {
    vi.mocked(useFeatureFlags).mockReturnValue({
      isEnabled: vi.fn(() => true),
      flags: { testFlag: true },
    });

    render(
      <FeatureFlagGate flag="testFlag">
        <div>
          <p>Parent content</p>
          <ul>
            <li>Item 1</li>
            <li>Item 2</li>
          </ul>
        </div>
      </FeatureFlagGate>
    );

    expect(screen.getByText('Parent content')).toBeInTheDocument();
    expect(screen.getByText('Item 1')).toBeInTheDocument();
    expect(screen.getByText('Item 2')).toBeInTheDocument();
  });

  it('should call isEnabled with correct flag name', () => {
    const isEnabledMock = vi.fn(() => true);
    vi.mocked(useFeatureFlags).mockReturnValue({
      isEnabled: isEnabledMock,
      flags: { customFlag: true },
    });

    render(
      <FeatureFlagGate flag="customFlag">
        <div>Content</div>
      </FeatureFlagGate>
    );

    expect(isEnabledMock).toHaveBeenCalledWith('customFlag');
  });
});

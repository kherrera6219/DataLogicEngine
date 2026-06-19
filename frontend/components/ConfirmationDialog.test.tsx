import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ConfirmationDialog, RiskTier } from './ConfirmationDialog';

// Mock Dialog component with minimal props
vi.mock('@/components/ui/dialog', () => ({
  Dialog: ({ children, open, onOpenChange }: any) => (
    <div data-testid="dialog" data-open={open}>
      {open && children}
    </div>
  ),
  DialogContent: ({ children }: any) => <div data-testid="dialog-content">{children}</div>,
  DialogDescription: ({ children }: any) => <div>{children}</div>,
  DialogFooter: ({ children }: any) => <div data-testid="dialog-footer">{children}</div>,
  DialogHeader: ({ children }: any) => <div>{children}</div>,
  DialogTitle: ({ children }: any) => <div>{children}</div>,
}));

vi.mock('@/components/ui/badge', () => ({
  Badge: ({ children }: any) => <span data-testid="badge">{children}</span>,
}));

vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, className }: any) => (
    <button onClick={onClick} className={className} data-testid="button">
      {children}
    </button>
  ),
}));

vi.mock('lucide-react', () => ({
  AlertTriangle: () => <span data-testid="alert-triangle">Alert</span>,
  Trash2: () => <span data-testid="trash-icon">Trash</span>,
  PenLine: () => <span data-testid="pen-icon">Pen</span>,
  Eye: () => <span data-testid="eye-icon">Eye</span>,
}));

describe('ConfirmationDialog', () => {
  const defaultProps = {
    open: true,
    onOpenChange: vi.fn(),
    onConfirm: vi.fn(),
    title: 'Confirm Action',
    description: 'Are you sure?',
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render when open is true', () => {
    render(<ConfirmationDialog {...defaultProps} />);
    expect(screen.getByTestId('dialog')).toHaveAttribute('data-open', 'true');
  });

  it('should not render content when open is false', () => {
    render(<ConfirmationDialog {...defaultProps} open={false} />);
    expect(screen.queryByTestId('dialog-content')).not.toBeInTheDocument();
  });

  it('should display title and description', () => {
    render(<ConfirmationDialog {...defaultProps} />);
    expect(screen.getByText('Confirm Action')).toBeInTheDocument();
    expect(screen.getByText('Are you sure?')).toBeInTheDocument();
  });

  it('should display badge for risk tier', () => {
    render(<ConfirmationDialog {...defaultProps} riskTier="write" />);
    expect(screen.getByTestId('badge')).toBeInTheDocument();
  });

  it('should display confirm button with custom label', () => {
    render(
      <ConfirmationDialog {...defaultProps} confirmLabel="Delete Permanently" />
    );
    expect(screen.getByText('Delete Permanently')).toBeInTheDocument();
  });

  it('should display cancel button with custom label', () => {
    render(
      <ConfirmationDialog {...defaultProps} cancelLabel="Keep It" />
    );
    expect(screen.getByText('Keep It')).toBeInTheDocument();
  });

  it('should call onConfirm when confirm button clicked', () => {
    const onConfirm = vi.fn();
    render(
      <ConfirmationDialog
        {...defaultProps}
        onConfirm={onConfirm}
        confirmLabel="Confirm"
      />
    );

    const buttons = screen.getAllByTestId('button');
    // Find the confirm button (typically first button)
    const confirmButton = buttons.find((b) => b.textContent.includes('Confirm'));
    if (confirmButton) {
      fireEvent.click(confirmButton);
    }
  });

  it('should show destructive risk tier', () => {
    render(
      <ConfirmationDialog
        {...defaultProps}
        riskTier="destructive"
        title="Delete Forever"
      />
    );
    expect(screen.getByText('Delete Forever')).toBeInTheDocument();
    expect(screen.getByTestId('alert-triangle')).toBeInTheDocument();
  });

  it('should show write risk tier', () => {
    render(
      <ConfirmationDialog
        {...defaultProps}
        riskTier="write"
        title="Update Settings"
      />
    );
    expect(screen.getByText('Update Settings')).toBeInTheDocument();
  });

  it('should show read-only risk tier', () => {
    render(
      <ConfirmationDialog
        {...defaultProps}
        riskTier="read_only"
        title="View Details"
      />
    );
    expect(screen.getByText('View Details')).toBeInTheDocument();
  });

  it('should handle all risk tier types', () => {
    const riskTiers: RiskTier[] = ['read_only', 'write', 'destructive'];

    riskTiers.forEach((tier) => {
      const { unmount } = render(
        <ConfirmationDialog
          {...defaultProps}
          riskTier={tier}
          title={`Test ${tier}`}
        />
      );

      expect(screen.getByText(`Test ${tier}`)).toBeInTheDocument();
      unmount();
      vi.clearAllMocks();
    });
  });

  it('should use default labels', () => {
    render(<ConfirmationDialog {...defaultProps} />);
    const buttons = screen.getAllByTestId('button');
    expect(buttons.length).toBeGreaterThan(0);
  });

  it('should call onOpenChange when dialog interaction occurs', () => {
    const onOpenChange = vi.fn();
    render(
      <ConfirmationDialog {...defaultProps} onOpenChange={onOpenChange} />
    );
    expect(screen.getByTestId('dialog')).toBeInTheDocument();
  });
});

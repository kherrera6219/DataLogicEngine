import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ConfirmationDialog, RiskTier } from './ConfirmationDialog';

describe('ConfirmationDialog', () => {
  const mockOnOpenChange = vi.fn();
  const mockOnConfirm = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render nothing when closed', () => {
    render(
      <ConfirmationDialog
        open={false}
        onOpenChange={mockOnOpenChange}
        onConfirm={mockOnConfirm}
        title="Delete item"
        description="Are you sure?"
      />
    );
    // Dialog content should not be visible when open={false}
    expect(screen.queryByText('Delete item')).not.toBeInTheDocument();
  });

  it('should render dialog when open', () => {
    render(
      <ConfirmationDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onConfirm={mockOnConfirm}
        title="Delete item"
        description="Are you sure?"
      />
    );
    expect(screen.getByText('Delete item')).toBeInTheDocument();
    expect(screen.getByText('Are you sure?')).toBeInTheDocument();
  });

  it('should display correct risk tier badge', () => {
    render(
      <ConfirmationDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onConfirm={mockOnConfirm}
        title="Delete item"
        description="Are you sure?"
        riskTier="destructive"
      />
    );
    expect(screen.getByText('Destructive — cannot be undone')).toBeInTheDocument();
  });

  it('should call onConfirm when confirm button clicked', async () => {
    render(
      <ConfirmationDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onConfirm={mockOnConfirm}
        title="Delete item"
        description="Are you sure?"
        confirmLabel="Delete"
      />
    );

    const confirmButton = screen.getByRole('button', { name: /Delete/i });
    fireEvent.click(confirmButton);

    await waitFor(() => {
      expect(mockOnConfirm).toHaveBeenCalledTimes(1);
      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it('should call onOpenChange with false when cancel button clicked', async () => {
    render(
      <ConfirmationDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onConfirm={mockOnConfirm}
        title="Delete item"
        description="Are you sure?"
      />
    );

    const cancelButton = screen.getByRole('button', { name: /Cancel/i });
    fireEvent.click(cancelButton);

    await waitFor(() => {
      expect(mockOnOpenChange).toHaveBeenCalledWith(false);
      expect(mockOnConfirm).not.toHaveBeenCalled();
    });
  });

  it('should render custom labels', () => {
    render(
      <ConfirmationDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onConfirm={mockOnConfirm}
        title="Archive project?"
        description="This will move the project to archived status."
        confirmLabel="Archive"
        cancelLabel="Keep it"
      />
    );

    expect(screen.getByRole('button', { name: /Archive/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Keep it/i })).toBeInTheDocument();
  });

  it('should show different risk tier badges', () => {
    const riskTiers: RiskTier[] = ['read_only', 'write', 'destructive'];

    riskTiers.forEach((tier) => {
      const { unmount } = render(
        <ConfirmationDialog
          open={true}
          onOpenChange={mockOnOpenChange}
          onConfirm={mockOnConfirm}
          title="Test"
          description="Test"
          riskTier={tier}
        />
      );

      if (tier === 'read_only') {
        expect(screen.getByText('Read-only')).toBeInTheDocument();
      } else if (tier === 'write') {
        expect(screen.getByText('Write operation')).toBeInTheDocument();
      } else if (tier === 'destructive') {
        expect(screen.getByText('Destructive — cannot be undone')).toBeInTheDocument();
      }

      unmount();
      vi.clearAllMocks();
    });
  });

  it('should show warning icon for destructive operations', () => {
    render(
      <ConfirmationDialog
        open={true}
        onOpenChange={mockOnOpenChange}
        onConfirm={mockOnConfirm}
        title="Delete forever"
        description="This cannot be undone."
        riskTier="destructive"
      />
    );

    // SVG icon should be present (lucide AlertTriangle)
    const titleElement = screen.getByText('Delete forever');
    expect(titleElement.parentElement?.querySelector('svg')).toBeInTheDocument();
  });
});

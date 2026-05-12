'use client';

import React from 'react';
import { AlertTriangle, Trash2, PenLine, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

export type RiskTier = 'read_only' | 'write' | 'destructive';

interface ConfirmationDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: () => void;
  title: string;
  description: string;
  riskTier?: RiskTier;
  confirmLabel?: string;
  cancelLabel?: string;
}

const TIER_CONFIG: Record<RiskTier, {
  icon: React.ReactNode;
  badgeLabel: string;
  badgeClass: string;
  confirmClass: string;
}> = {
  read_only: {
    icon: <Eye className="h-4 w-4" />,
    badgeLabel: 'Read-only',
    badgeClass: 'border-blue-500/40 text-blue-400',
    confirmClass: '',
  },
  write: {
    icon: <PenLine className="h-4 w-4" />,
    badgeLabel: 'Write operation',
    badgeClass: 'border-yellow-500/40 text-yellow-500',
    confirmClass: '',
  },
  destructive: {
    icon: <Trash2 className="h-4 w-4" />,
    badgeLabel: 'Destructive — cannot be undone',
    badgeClass: 'border-red-500/40 text-red-500',
    confirmClass: 'bg-destructive hover:bg-destructive/90 text-destructive-foreground',
  },
};

export function ConfirmationDialog({
  open,
  onOpenChange,
  onConfirm,
  title,
  description,
  riskTier = 'write',
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
}: ConfirmationDialogProps) {
  const config = TIER_CONFIG[riskTier];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {riskTier === 'destructive' && (
              <AlertTriangle className="h-5 w-5 text-destructive shrink-0" />
            )}
            {title}
          </DialogTitle>
          <DialogDescription className="space-y-2">
            <span className="block">{description}</span>
            <Badge
              variant="outline"
              className={cn('flex items-center gap-1 w-fit text-[11px]', config.badgeClass)}
            >
              {config.icon}
              {config.badgeLabel}
            </Badge>
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="flex-row justify-end gap-2 pt-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {cancelLabel}
          </Button>
          <Button
            className={config.confirmClass}
            onClick={() => {
              onConfirm();
              onOpenChange(false);
            }}
          >
            {confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

'use client';

import React from 'react';
import { FeatureFlagKey } from '@/lib/feature-flags/definitions';
import { useFeatureFlags } from '@/contexts/FeatureFlagContext';

interface FeatureFlagGateProps {
  flag: FeatureFlagKey;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export function FeatureFlagGate({ flag, fallback = null, children }: FeatureFlagGateProps) {
  const { isEnabled } = useFeatureFlags();
  if (!isEnabled(flag)) {
    return <>{fallback}</>;
  }
  return <>{children}</>;
}

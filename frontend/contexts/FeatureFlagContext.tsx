'use client';

import React, { createContext, useContext, useMemo, useState, useEffect } from 'react';
import {
  createDefaultFeatureFlagState,
  FEATURE_FLAG_DEFINITIONS,
  FEATURE_FLAG_KEYS,
  FeatureFlagKey,
  FeatureFlagSource,
  FeatureFlagSources,
  FeatureFlagState,
} from '@/lib/feature-flags/definitions';
import { getLocalStorageItem, setLocalStorageItem } from '@/lib/state/storage';

const LOCAL_FEATURE_FLAGS_KEY = 'dle_feature_flags';

interface FeatureFlagContextValue {
  flags: FeatureFlagState;
  sources: FeatureFlagSources;
  isEnabled: (flag: FeatureFlagKey) => boolean;
  getSource: (flag: FeatureFlagKey) => FeatureFlagSource;
  setLocalOverride: (flag: FeatureFlagKey, value: boolean) => void;
  clearLocalOverride: (flag: FeatureFlagKey) => void;
}

const FeatureFlagContext = createContext<FeatureFlagContextValue | undefined>(undefined);

function parseBoolean(value: unknown): boolean | undefined {
  if (typeof value === 'boolean') {
    return value;
  }
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase();
    if (normalized === 'true' || normalized === '1') return true;
    if (normalized === 'false' || normalized === '0') return false;
  }
  if (typeof value === 'number') {
    if (value === 1) return true;
    if (value === 0) return false;
  }
  return undefined;
}

function parseFlagPayload(raw: string | undefined): Partial<FeatureFlagState> {
  if (!raw) {
    return {};
  }

  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    const normalized: Partial<FeatureFlagState> = {};
    for (const key of FEATURE_FLAG_KEYS) {
      const parsedValue = parseBoolean(parsed[key]);
      if (parsedValue !== undefined) {
        normalized[key] = parsedValue;
      }
    }
    return normalized;
  } catch {
    return {};
  }
}

function readLocalOverrides(): Partial<FeatureFlagState> {
  return parseFlagPayload(getLocalStorageItem(LOCAL_FEATURE_FLAGS_KEY) ?? undefined);
}

function buildResolvedFlags(localOverrides: Partial<FeatureFlagState>) {
  const defaultFlags = createDefaultFeatureFlagState();
  const sources = {} as FeatureFlagSources;

  for (const key of FEATURE_FLAG_KEYS) {
    sources[key] = 'default';
  }

  const cloudOverrides = parseFlagPayload(process.env.NEXT_PUBLIC_FEATURE_FLAGS);
  const enterpriseOverrides = parseFlagPayload(process.env.NEXT_PUBLIC_ENTERPRISE_FEATURE_FLAGS);

  const resolved = { ...defaultFlags };

  for (const key of FEATURE_FLAG_KEYS) {
    if (cloudOverrides[key] !== undefined) {
      resolved[key] = cloudOverrides[key] as boolean;
      sources[key] = 'cloud';
    }
    if (enterpriseOverrides[key] !== undefined) {
      resolved[key] = enterpriseOverrides[key] as boolean;
      sources[key] = 'enterprise';
    }
  }

  for (const key of FEATURE_FLAG_KEYS) {
    if (!FEATURE_FLAG_DEFINITIONS[key].localOverrideAllowed) {
      continue;
    }
    if (localOverrides[key] !== undefined) {
      resolved[key] = localOverrides[key] as boolean;
      sources[key] = 'local';
    }
  }

  return { flags: resolved, sources };
}

function persistLocalOverrides(localOverrides: Partial<FeatureFlagState>) {
  setLocalStorageItem(LOCAL_FEATURE_FLAGS_KEY, JSON.stringify(localOverrides));
}

export function FeatureFlagProvider({ children }: { children: React.ReactNode }) {
  const [localOverrides, setLocalOverrides] = useState<Partial<FeatureFlagState>>(() => readLocalOverrides());
  // Remote flags fetched from the backend API at runtime.
  const [remoteOverrides, setRemoteOverrides] = useState<Partial<FeatureFlagState>>({});

  useEffect(() => {
    let cancelled = false;
    fetch('/api/v1/feature-flags', { credentials: 'include' })
      .then((r) => (r.ok ? r.json() : null))
      .then((data: { flags?: Record<string, { value: boolean; is_locked: boolean }> } | null) => {
        if (cancelled || !data?.flags) return;
        const remote: Partial<FeatureFlagState> = {};
        for (const key of FEATURE_FLAG_KEYS) {
          if (data.flags[key] !== undefined) {
            remote[key] = data.flags[key].value;
          }
        }
        setRemoteOverrides(remote);
      })
      .catch(() => { /* non-fatal — fall back to env / defaults */ });
    return () => { cancelled = true; };
  }, []);

  const resolved = useMemo(() => {
    const base = buildResolvedFlags(localOverrides);
    // Inject remote overrides between enterprise env and local user overrides.
    const flags = { ...base.flags };
    const sources = { ...base.sources };
    for (const key of FEATURE_FLAG_KEYS) {
      if (remoteOverrides[key] !== undefined) {
        flags[key] = remoteOverrides[key] as boolean;
        sources[key] = 'cloud' as const;
      }
    }
    // Re-apply local overrides on top (only for flags that allow it).
    for (const key of FEATURE_FLAG_KEYS) {
      if (!FEATURE_FLAG_DEFINITIONS[key].localOverrideAllowed) continue;
      if (localOverrides[key] !== undefined) {
        flags[key] = localOverrides[key] as boolean;
        sources[key] = 'local' as const;
      }
    }
    return { flags, sources };
  }, [localOverrides, remoteOverrides]);

  const value = useMemo<FeatureFlagContextValue>(() => {
    const setLocalOverride = (flag: FeatureFlagKey, nextValue: boolean) => {
      if (!FEATURE_FLAG_DEFINITIONS[flag].localOverrideAllowed) {
        return;
      }
      setLocalOverrides((previous) => {
        const next = { ...previous, [flag]: nextValue };
        persistLocalOverrides(next);
        return next;
      });
    };

    const clearLocalOverride = (flag: FeatureFlagKey) => {
      setLocalOverrides((previous) => {
        if (previous[flag] === undefined) {
          return previous;
        }
        const next = { ...previous };
        delete next[flag];
        persistLocalOverrides(next);
        return next;
      });
    };

    return {
      flags: resolved.flags,
      sources: resolved.sources,
      isEnabled: (flag: FeatureFlagKey) => Boolean(resolved.flags[flag]),
      getSource: (flag: FeatureFlagKey) => resolved.sources[flag],
      setLocalOverride,
      clearLocalOverride,
    };
  }, [resolved.flags, resolved.sources]);

  return <FeatureFlagContext.Provider value={value}>{children}</FeatureFlagContext.Provider>;
}

export function useFeatureFlags() {
  const context = useContext(FeatureFlagContext);
  if (!context) {
    throw new Error('useFeatureFlags must be used within FeatureFlagProvider');
  }
  return context;
}

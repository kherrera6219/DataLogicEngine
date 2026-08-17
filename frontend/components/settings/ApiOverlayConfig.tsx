'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { useToast } from '@/components/ui/use-toast';
import { Eye, RefreshCw, ShieldCheck } from 'lucide-react';
import { ApiError, request } from '@/lib/api';
import {
  CONFIGURABLE_PROVIDER_TYPES,
  DEFAULT_MODEL_BY_PROVIDER,
  MODEL_LIBRARY,
} from '@/lib/provider-manifest.generated';

interface ProviderOption {
  id?: string;
  name: string;
  type: string;
  model?: string;
  is_default?: boolean;
  availability_status?: string;
}

interface SaveKeyResponse {
  success?: boolean;
  provider?: {
    id?: string;
    name?: string;
    provider_type?: string;
    type?: string;
  };
}

function errorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  return String(error);
}

function providerTestMessage(error: unknown): { message: string; status?: number } {
  if (!(error instanceof ApiError)) return { message: errorMessage(error) };
  const labels: Record<number, string> = {
    401: 'Invalid API key',
    422: 'Invalid model',
    429: 'Provider rate limit reached',
    504: 'Provider network timeout',
  };
  return {
    message: `${labels[error.status] || 'Connection failed'} — ${error.message}`,
    status: error.status,
  };
}

export function ApiOverlayConfig() {
  const { toast } = useToast();
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState(DEFAULT_MODEL_BY_PROVIDER.openai);
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [providers, setProviders] = useState<ProviderOption[]>([]);
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [saved, setSaved] = useState(false);
  const [connection, setConnection] = useState<'unknown' | 'available' | 'failed'>('unknown');
  const [testError, setTestError] = useState<{ message: string; status?: number } | null>(null);

  useEffect(() => {
    let cancelled = false;
    void request<{ providers?: ProviderOption[] }>('/gateway/providers')
      .then((result) => {
        if (cancelled) return;
        const available = result.providers || [];
        setProviders(available);
        const preferred = available.find((item) => item.is_default) || available[0];
        if (preferred) {
          const type = (preferred.type || preferred.name).toLowerCase();
          setProvider(type);
          setSelectedProviderId(preferred.id || null);
          const supportedModels = MODEL_LIBRARY[type] || [];
          setModel(
            preferred.model && supportedModels.includes(preferred.model)
              ? preferred.model
              : DEFAULT_MODEL_BY_PROVIDER[type] || '',
          );
        }
      })
      .catch(() => {
        if (!cancelled) setProviders([]);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => { cancelled = true; };
  }, []);

  const markDirty = () => {
    setSaved(false);
    setConnection('unknown');
    setTestError(null);
  };

  const modelOptions = useMemo(() => {
    return MODEL_LIBRARY[provider] || [];
  }, [provider]);

  const effectiveModel = modelOptions.includes(model) ? model : (modelOptions[0] || model);

  const changeProvider = (nextProvider: string) => {
    setProvider(nextProvider);
    const matching = providers.find(
      (item) => (item.type || item.name).toLowerCase() === nextProvider,
    );
    setSelectedProviderId(matching?.id || null);
    const supportedModels = MODEL_LIBRARY[nextProvider] || [];
    setModel(
      matching?.model && supportedModels.includes(matching.model)
        ? matching.model
        : DEFAULT_MODEL_BY_PROVIDER[nextProvider] || '',
    );
    markDirty();
  };

  const saveKey = async (): Promise<string | null> => {
    if (!apiKey.trim()) {
      toast('Enter a provider API key before saving.', 'warning');
      return null;
    }
    setSaving(true);
    try {
      const result = await request<SaveKeyResponse>('/gateway/keys', {
        method: 'POST',
        body: JSON.stringify({ provider, key: apiKey.trim(), model: effectiveModel }),
      });
      const savedProvider = result.provider;
      const id = savedProvider?.id || selectedProviderId;
      setSelectedProviderId(id || null);
      setSaved(true);
      setApiKey('');
      toast('Provider key saved in protected local storage.', 'success');
      return id || null;
    } catch (error) {
      toast(`Provider key could not be saved: ${errorMessage(error)}`, 'error');
      return null;
    } finally {
      setSaving(false);
    }
  };

  const testConnection = async () => {
    setTesting(true);
    setTestError(null);
    const id = selectedProviderId || await saveKey();
    if (!id) {
      setConnection('failed');
      setTesting(false);
      return;
    }
    try {
      const result = await request<{ success?: boolean; message?: string; error?: string }>(
        `/gateway/providers/${id}/test`,
        { method: 'POST' },
      );
      if (!result.success) throw new Error(result.error || result.message || 'Provider test failed');
      setConnection('available');
      setSaved(true);
      toast(result.message || 'Provider connection is available.', 'success');
    } catch (error) {
      const normalized = providerTestMessage(error);
      setConnection('failed');
      setTestError(normalized);
      toast(normalized.message, 'error');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-6" aria-busy={loading || saving || testing}>
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <CardTitle>Provider Connections</CardTitle>
              <CardDescription>Outbound OpenAI and Google credentials used by DataLogicEngine. These are not client gateway keys.</CardDescription>
            </div>
            <Badge variant="outline">{providers.length} configured</Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="space-y-2"><span className="text-sm font-medium">Provider</span>
              <Select id="provider-connection-provider" aria-label="Provider" value={provider} onChange={(event: React.ChangeEvent<HTMLSelectElement>) => changeProvider(event.target.value)}>
                {CONFIGURABLE_PROVIDER_TYPES.map((item) => <option key={item} value={item}>{item === 'openai' ? 'OpenAI' : 'Google'}</option>)}
              </Select>
            </label>
            <label className="space-y-2"><span className="text-sm font-medium">Model</span>
              <Select id="provider-connection-model" aria-label="Model" value={effectiveModel} onChange={(event: React.ChangeEvent<HTMLSelectElement>) => { setModel(event.target.value); markDirty(); }}>
                {modelOptions.map((item) => <option key={item} value={item}>{item}</option>)}
              </Select>
            </label>
          </div>
          <label className="space-y-2"><span className="text-sm font-medium">Provider API key</span>
            <div className="flex flex-wrap gap-2">
              <div className="relative min-w-[260px] flex-1">
                <Input aria-label="Provider API key" type={showKey ? 'text' : 'password'} value={apiKey} onChange={(event) => { setApiKey(event.target.value); markDirty(); }} placeholder={provider === 'openai' ? 'sk-…' : 'Google API key'} className="pr-10" />
                <button type="button" className="absolute right-3 top-2.5 text-muted-foreground" onClick={() => setShowKey((value) => !value)} aria-label={showKey ? 'Hide provider API key' : 'Show provider API key'}><Eye className="h-4 w-4" /></button>
              </div>
              <Button onClick={() => void saveKey()} disabled={saving || !apiKey.trim()}>{saving ? 'Saving…' : saved ? 'Saved' : 'Save provider key'}</Button>
              <Button variant="outline" onClick={() => void testConnection()} disabled={testing || (!selectedProviderId && !apiKey.trim())}>{testing ? <><RefreshCw className="mr-2 h-4 w-4 animate-spin" />Testing…</> : 'Test provider connection'}</Button>
            </div>
          </label>
          {connection === 'available' && <p className="text-sm text-green-600 dark:text-green-400">Provider connection passed live validation.</p>}
          {connection === 'failed' && testError && <div className="rounded border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-700 dark:text-red-300"><strong>Connection Error{testError.status ? ` · HTTP ${testError.status}` : ''}</strong><div>{testError.message}</div></div>}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5" /> Credential boundary</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground">Provider credentials remain server-owned, are never returned after save, and are never issued to external applications. Create inbound application credentials in Client Gateway.</CardContent>
      </Card>
    </div>
  );
}

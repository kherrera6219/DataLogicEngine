'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Brain, CheckCircle2, Eye, FlaskConical, RefreshCw, Save } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { request } from '@/lib/api';
import { useToast } from '@/components/ui/use-toast';

interface ProviderOption {
  id?: string;
  name: string;
  type: string;
  model?: string;
  is_default?: boolean;
  has_api_key?: boolean;
}

interface SaveKeyResponse {
  success?: boolean;
  provider?: {
    id?: string;
    name?: string;
    type?: string;
    provider_type?: string;
  };
}

const MODEL_LIBRARY: Record<string, string[]> = {
  openai: ['gpt-5.2', 'gpt-4.1', 'gpt-4o-mini'],
  anthropic: ['claude-opus-4.5', 'claude-sonnet-4.5'],
  google: ['gemini-3.0-pro', 'gemini-2.5-pro'],
  azure: ['gpt-4.1'],
};

function formatError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

export function AiModelSettings() {
  const { toast } = useToast();
  const [providers, setProviders] = useState<ProviderOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState('gpt-5.2');
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadProviders() {
      try {
        const result = await request<{ providers?: ProviderOption[] }>('/gateway/providers');
        if (cancelled) return;

        const loadedProviders = (result.providers || []).map((entry) => ({
          ...entry,
          type: (entry.type || entry.name || '').toLowerCase(),
        }));
        setProviders(loadedProviders);

        if (loadedProviders.length > 0) {
          const preferred = loadedProviders.find((entry) => entry.is_default) || loadedProviders[0];
          const nextType = preferred.type || preferred.name.toLowerCase();
          setProvider(nextType);
          if (preferred.model) {
            setModel(preferred.model);
          }
        }
      } catch (error) {
        if (!cancelled) {
          setProviders([]);
          toast(`Failed to load provider models: ${formatError(error)}`, 'error');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadProviders();
    return () => {
      cancelled = true;
    };
  }, [toast]);

  const providerChoices = useMemo(
    () =>
      Array.from(
        new Set(
          [...providers.map((entry) => entry.type), 'openai', 'anthropic', 'google', 'azure'].filter(Boolean)
        )
      ),
    [providers]
  );

  const selectedProvider = useMemo(
    () => providers.find((entry) => entry.type === provider),
    [provider, providers]
  );

  const modelOptions = useMemo(() => {
    const fromProvider = providers
      .filter((entry) => entry.type === provider)
      .map((entry) => entry.model)
      .filter((entry): entry is string => Boolean(entry));
    const defaults = MODEL_LIBRARY[provider] || [];
    return Array.from(new Set([...fromProvider, ...defaults]));
  }, [provider, providers]);

  useEffect(() => {
    if (!modelOptions.length) return;
    if (!modelOptions.includes(model)) {
      setModel(modelOptions[0]);
    }
  }, [modelOptions, model]);

  const upsertProvider = (providerType: string, providerId: string | null) => {
    setProviders((previous) => {
      const next = [...previous];
      const index = next.findIndex((entry) => entry.type === providerType);
      const nextEntry: ProviderOption = {
        id: providerId || undefined,
        name: providerType,
        type: providerType,
        model,
        has_api_key: true,
      };

      if (index >= 0) {
        next[index] = {
          ...next[index],
          ...nextEntry,
        };
      } else {
        next.push(nextEntry);
      }
      return next;
    });
  };

  const handleSaveConfiguration = async (): Promise<string | null> => {
    if (!apiKey.trim()) {
      toast('Enter an API key before saving the model configuration.', 'warning');
      return null;
    }

    setSaving(true);
    try {
      const result = await request<SaveKeyResponse>('/gateway/keys', {
        method: 'POST',
        body: JSON.stringify({
          provider,
          key: apiKey.trim(),
          model,
        }),
      });

      const savedProvider = result.provider;
      const savedType = String(savedProvider?.provider_type || savedProvider?.type || provider).toLowerCase();
      const savedId = savedProvider?.id || selectedProvider?.id || null;
      upsertProvider(savedType, savedId);
      toast('Model configuration saved.', 'success');
      return savedId;
    } catch (error) {
      toast(`Failed to save model configuration: ${formatError(error)}`, 'error');
      return null;
    } finally {
      setSaving(false);
    }
  };

  const handleTestModel = async () => {
    if (testing) return;
    setTesting(true);
    try {
      const providerId = selectedProvider?.id || await handleSaveConfiguration();
      if (!providerId) {
        return;
      }

      const result = await request<{ success?: boolean; message?: string; error?: string }>(
        `/gateway/providers/${providerId}/test`,
        { method: 'POST' }
      );
      if (!result?.success) {
        throw new Error(result?.error || result?.message || 'Provider model test failed');
      }
      toast(result.message || 'Provider model test succeeded.', 'success');
    } catch (error) {
      toast(`Provider model test failed: ${formatError(error)}`, 'error');
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-10">
        <RefreshCw className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Brain className="h-5 w-5 text-blue-500" />
          AI Model Controls
        </h2>
        <p className="text-sm text-muted-foreground">
          Configure provider model selection and validate connectivity.
        </p>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Configured Providers</CardTitle>
            <CardDescription>Current model availability and key status.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {providers.length === 0 && (
              <p className="text-sm text-muted-foreground">No providers detected yet. Save a key to create one.</p>
            )}
            {providers.map((entry) => (
              <div key={`${entry.type}-${entry.id || entry.model || 'provider'}`} className="rounded-lg border p-3 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-semibold">{entry.type}</span>
                  {entry.is_default && <Badge variant="secondary">Default</Badge>}
                </div>
                <div className="text-xs text-muted-foreground">
                  Model: {entry.model || 'Not configured'}
                </div>
                <Badge variant={entry.has_api_key ? 'success' : 'outline'}>
                  {entry.has_api_key ? 'API key set' : 'API key missing'}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Active Model Configuration</CardTitle>
            <CardDescription>Choose provider/model and save credentials.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase text-muted-foreground">Provider</label>
                <Select
                  value={provider}
                  onChange={(event: React.ChangeEvent<HTMLSelectElement>) => setProvider(event.target.value)}
                >
                  {providerChoices.map((entry) => (
                    <option key={entry} value={entry}>{entry}</option>
                  ))}
                </Select>
              </div>
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase text-muted-foreground">Model</label>
                <Select
                  value={model}
                  onChange={(event: React.ChangeEvent<HTMLSelectElement>) => setModel(event.target.value)}
                >
                  {modelOptions.length === 0 && <option value={model}>{model}</option>}
                  {modelOptions.map((entry) => (
                    <option key={entry} value={entry}>{entry}</option>
                  ))}
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase text-muted-foreground">API Key</label>
              <div className="relative">
                <Input
                  type={showKey ? 'text' : 'password'}
                  value={apiKey}
                  onChange={(event) => setApiKey(event.target.value)}
                  placeholder="Paste provider API key"
                  className="pr-10 font-mono"
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-3 text-muted-foreground hover:text-foreground"
                  onClick={() => setShowKey((prev) => !prev)}
                  aria-label={showKey ? 'Hide API key' : 'Show API key'}
                >
                  <Eye className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button onClick={() => void handleSaveConfiguration()} disabled={saving || !apiKey.trim()}>
                {saving ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                {saving ? 'Saving...' : 'Save Model'}
              </Button>
              <Button variant="outline" onClick={() => void handleTestModel()} disabled={testing}>
                {testing ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <FlaskConical className="h-4 w-4 mr-2" />}
                {testing ? 'Testing...' : 'Test Model'}
              </Button>
            </div>

            {selectedProvider?.has_api_key && (
              <div className="rounded-md border border-green-500/30 bg-green-500/10 px-3 py-2 text-sm text-green-700 dark:text-green-300 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Provider key detected for `{selectedProvider.type}`.
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default AiModelSettings;

'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Brain, CheckCircle2, Eye, FlaskConical, RefreshCw, Save, Power, History } from 'lucide-react';
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

// The app uses one user-selected cloud model: OpenAI gpt-5.5 or Google gemini-3.1-pro-preview.
const MODEL_LIBRARY: Record<string, string[]> = {
  openai: ['gpt-5.5'],
  google: ['gemini-3.1-pro-preview'],
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
  const [model, setModel] = useState('gpt-5.5');
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);

  // User AI preference controls
  const [aiEnabled, setAiEnabled] = useState(true);
  const [storeHistory, setStoreHistory] = useState(true);
  const [savingPrefs, setSavingPrefs] = useState(false);

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

  useEffect(() => {
    request<{ ai_processing_enabled?: boolean; store_chat_history?: boolean }>('/settings/ai')
      .then((data) => {
        if (typeof data.ai_processing_enabled === 'boolean') setAiEnabled(data.ai_processing_enabled);
        if (typeof data.store_chat_history === 'boolean') setStoreHistory(data.store_chat_history);
      })
      .catch(() => {}); // non-fatal
  }, []);

  const handleSavePreferences = async () => {
    setSavingPrefs(true);
    try {
      await request('/settings/ai', {
        method: 'POST',
        body: JSON.stringify({ ai_processing_enabled: aiEnabled, store_chat_history: storeHistory }),
      });
      toast('AI preferences saved.', 'success');
    } catch {
      toast('Failed to save AI preferences.', 'error');
    } finally {
      setSavingPrefs(false);
    }
  };

  // Only two cloud models are offered: OpenAI (gpt-5.5) and Google (gemini-3.1-pro-preview).
  const providerChoices = useMemo(() => ['openai', 'google'], []);

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

  // Sync model to available options during render instead of via effect.
  if (modelOptions.length && !modelOptions.includes(model)) {
    setModel(modelOptions[0]);
  }

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
    <div className="space-y-6" aria-busy={loading || saving || testing || savingPrefs}>
      <div>
        <h2 className="text-xl font-bold flex items-center gap-2">
          <Brain className="h-5 w-5 text-blue-500" />
          AI Model Controls
        </h2>
        <p className="text-sm text-muted-foreground">
          Configure provider model selection and validate connectivity. AI requests require internet access and may send prompts and selected context to the configured provider.
        </p>
      </div>

      {/* AI Processing Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <Power className="h-4 w-4" />
            Processing Controls
          </CardTitle>
          <CardDescription>Control whether AI requests are sent to configured third-party providers and whether chat history is stored locally.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between p-3 rounded-lg border bg-muted/30">
            <div className="space-y-0.5">
              <p className="text-sm font-medium flex items-center gap-2">
                <Power className="h-3.5 w-3.5 text-muted-foreground" />
                Enable AI Processing
              </p>
              <p className="text-xs text-muted-foreground">When disabled, no queries will be sent to AI providers.</p>
            </div>
            <button
              role="switch"
              aria-checked={aiEnabled}
              aria-label="Enable AI processing"
              onClick={() => setAiEnabled((v) => !v)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 ${aiEnabled ? 'bg-blue-600' : 'bg-muted-foreground/40'}`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${aiEnabled ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg border bg-muted/30">
            <div className="space-y-0.5">
              <p className="text-sm font-medium flex items-center gap-2">
                <History className="h-3.5 w-3.5 text-muted-foreground" />
                Store Chat History
              </p>
              <p className="text-xs text-muted-foreground">When disabled, conversation turns will not be persisted to the database.</p>
            </div>
            <button
              role="switch"
              aria-checked={storeHistory}
              aria-label="Store chat history"
              onClick={() => setStoreHistory((v) => !v)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:ring-2 focus-visible:ring-blue-500 ${storeHistory ? 'bg-blue-600' : 'bg-muted-foreground/40'}`}
            >
              <span className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${storeHistory ? 'translate-x-6' : 'translate-x-1'}`} />
            </button>
          </div>

          <Button size="sm" onClick={() => void handleSavePreferences()} disabled={savingPrefs}>
            {savingPrefs ? <RefreshCw className="h-3.5 w-3.5 mr-1.5 animate-spin" /> : <Save className="h-3.5 w-3.5 mr-1.5" />}
            {savingPrefs ? 'Saving...' : 'Save Preferences'}
          </Button>
        </CardContent>
      </Card>

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
            {providers.map((entry) => {
              return (
                <div key={`${entry.type}-${entry.id || entry.model || 'provider'}`} className="rounded-lg border p-3 space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-semibold">{entry.type}</span>
                    <div className="flex items-center gap-1.5">
                      {entry.is_default && <Badge variant="secondary">Default</Badge>}
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Model: {entry.model || 'Not configured'}
                  </div>
                  <Badge variant={entry.has_api_key ? 'success' : 'outline'}>
                    {entry.has_api_key ? 'API key set' : 'API key missing'}
                  </Badge>
                </div>
              );
            })}
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
                <label htmlFor="provider-select" className="text-xs font-semibold uppercase text-muted-foreground">Provider</label>
                <Select
                  id="provider-select"
                  value={provider}
                  onChange={(event: React.ChangeEvent<HTMLSelectElement>) => setProvider(event.target.value)}
                >
                  {providerChoices.map((entry) => (
                    <option key={entry} value={entry}>{entry}</option>
                  ))}
                </Select>
              </div>
              <div className="space-y-2">
                <label htmlFor="model-select" className="text-xs font-semibold uppercase text-muted-foreground">Model</label>
                <Select
                  id="model-select"
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
              <label htmlFor="api-key-input" className="text-xs font-semibold uppercase text-muted-foreground">API Key</label>
              <div className="relative">
                <Input
                  id="api-key-input"
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
              <Button onClick={() => void handleSaveConfiguration()} disabled={saving || !apiKey.trim()} aria-label="Save model configuration">
                {saving ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}
                {saving ? 'Saving...' : 'Save Model'}
              </Button>
              <Button variant="outline" onClick={() => void handleTestModel()} disabled={testing} aria-label="Test provider model">
                {testing ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : <FlaskConical className="h-4 w-4 mr-2" />}
                {testing ? 'Testing...' : 'Test Model'}
              </Button>
            </div>

            {selectedProvider?.has_api_key && (
              <div className="rounded-md border border-green-500/30 bg-green-500/10 px-3 py-2 text-sm text-green-700 dark:text-green-300 flex items-center gap-2" role="status" aria-live="polite">
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

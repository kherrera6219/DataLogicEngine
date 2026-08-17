'use client';

import React, { useEffect, useMemo, useState } from 'react';
import { Brain, CheckCircle2, Download, Eye, FlaskConical, RefreshCw, Save, Power, History, ShieldCheck, Trash2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { request } from '@/lib/api';
import {
  CONFIGURABLE_PROVIDER_TYPES,
  DEFAULT_MODEL_BY_PROVIDER,
  MODEL_LIBRARY,
  PROVIDER_MANIFEST,
} from '@/lib/provider-manifest.generated';
import { useToast } from '@/components/ui/use-toast';

interface ProviderOption {
  id?: string;
  name: string;
  type: string;
  model?: string;
  is_default?: boolean;
  has_api_key?: boolean;
  status?: 'not_configured' | 'stored' | 'validating' | 'available' | 'limited' | 'invalid' | 'unavailable';
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

function isConfigurableProviderType(providerType: string | undefined): boolean {
  return CONFIGURABLE_PROVIDER_TYPES.includes((providerType || '').toLowerCase());
}

interface UsageWindow {
  calls: number;
  tokens_total: number;
  known_estimated_cost_usd: number | null;
  unknown_price_calls: number;
}

interface UsageLedger {
  schema_version: 'provider-usage-ledger.v1';
  generated_at: string;
  limits: {
    daily_calls: number;
    monthly_calls: number;
    daily_tokens: number;
    monthly_tokens: number;
    monthly_spend_usd: number | null;
  };
  remaining: {
    daily_calls: number;
    monthly_calls: number;
    daily_tokens: number;
    monthly_tokens: number;
    monthly_spend_usd: number | null;
  };
  daily: UsageWindow;
  monthly: UsageWindow;
  pricing_status: 'available' | 'unknown';
  entries: Array<{
    id: string;
    provider: string;
    model?: string | null;
    purpose: string;
    status: string;
    disclosed_categories: string[];
    created_at?: string | null;
  }>;
}

function formatCount(value: number | undefined): string {
  return new Intl.NumberFormat().format(Number(value || 0));
}

export function getProviderStatus(entry: ProviderOption, verified: boolean): {
  label: string;
  variant: 'secondary' | 'outline' | 'success';
} {
  if (!isConfigurableProviderType(entry.type)) {
    return { label: 'Unsupported legacy provider', variant: 'outline' };
  }

  const status = verified ? 'available' : (entry.status || (entry.has_api_key ? 'stored' : 'not_configured'));
  const labels: Record<string, string> = {
    not_configured: 'Not configured',
    stored: 'Stored',
    validating: 'Validating',
    available: 'Available',
    limited: 'Limited',
    invalid: 'Invalid',
    unavailable: 'Unavailable',
  };
  return {
    label: labels[status] || 'Unavailable',
    variant: status === 'available' ? 'success' : (status === 'stored' || status === 'validating' ? 'secondary' : 'outline'),
  };
}

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
  const [model, setModel] = useState(DEFAULT_MODEL_BY_PROVIDER.openai);
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [verifiedProviders, setVerifiedProviders] = useState<Record<string, boolean>>({});
  const [usageLedger, setUsageLedger] = useState<UsageLedger | null>(null);
  const [loadingLedger, setLoadingLedger] = useState(true);
  const [resettingLedger, setResettingLedger] = useState(false);

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
          const preferred =
            loadedProviders.find((entry) => entry.is_default && isConfigurableProviderType(entry.type)) ||
            loadedProviders.find((entry) => isConfigurableProviderType(entry.type));
          if (!preferred) {
            return;
          }

          const nextType = preferred.type || preferred.name.toLowerCase();
          setProvider(nextType);
          const supportedModels = MODEL_LIBRARY[nextType] || [];
          setModel(
            preferred.model && supportedModels.includes(preferred.model)
              ? preferred.model
              : DEFAULT_MODEL_BY_PROVIDER[nextType] || '',
          );
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

  const loadUsageLedger = async () => {
    setLoadingLedger(true);
    try {
      const result = await request<UsageLedger>('/gateway/usage-ledger?days=30');
      setUsageLedger(result?.schema_version === 'provider-usage-ledger.v1' ? result : null);
    } catch (error) {
      toast(`Failed to load provider usage: ${formatError(error)}`, 'error');
    } finally {
      setLoadingLedger(false);
    }
  };

  useEffect(() => {
    let cancelled = false;
    request<UsageLedger>('/gateway/usage-ledger?days=30')
      .then((result) => {
        if (!cancelled) {
          setUsageLedger(result?.schema_version === 'provider-usage-ledger.v1' ? result : null);
        }
      })
      .catch((error) => {
        if (!cancelled) toast(`Failed to load provider usage: ${formatError(error)}`, 'error');
      })
      .finally(() => {
        if (!cancelled) setLoadingLedger(false);
      });
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

  // The generated provider manifest is the only model selector authority.
  const providerChoices = useMemo(() => CONFIGURABLE_PROVIDER_TYPES, []);

  const selectedProvider = useMemo(
    () => providers.find((entry) => entry.type === provider),
    [provider, providers]
  );
  const selectedProviderVerified = Boolean(selectedProvider && verifiedProviders[selectedProvider.type]);

  const modelOptions = useMemo(() => {
    return MODEL_LIBRARY[provider] || [];
  }, [provider]);

  const effectiveModel = useMemo(() => {
    if (modelOptions.length && !modelOptions.includes(model)) {
      return modelOptions[0];
    }
    return model;
  }, [model, modelOptions]);

  const reasoningEffort = useMemo(() => {
    const providerContract = PROVIDER_MANIFEST.providers.find((entry) => entry.id === provider);
    return providerContract?.models.find((entry) => entry.id === effectiveModel)?.reasoning_effort;
  }, [effectiveModel, provider]);

  const upsertProvider = (providerType: string, providerId: string | null) => {
    setProviders((previous) => {
      const next = [...previous];
      const index = next.findIndex((entry) => entry.type === providerType);
      const nextEntry: ProviderOption = {
        id: providerId || undefined,
        name: providerType,
        type: providerType,
        model: effectiveModel,
        has_api_key: true,
        status: 'stored',
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
    setVerifiedProviders((previous) => ({ ...previous, [providerType]: false }));
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
          model: effectiveModel,
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
      setVerifiedProviders((previous) => ({ ...previous, [provider]: true }));
      toast(result.message || 'Provider model test succeeded.', 'success');
    } catch (error) {
      setVerifiedProviders((previous) => ({ ...previous, [provider]: false }));
      toast(`Provider model test failed: ${formatError(error)}`, 'error');
    } finally {
      setTesting(false);
    }
  };

  const handleExportLedger = async () => {
    try {
      const exported = await request<UsageLedger & { export_notice?: string }>('/gateway/usage-ledger/export?days=366');
      const blob = new Blob([JSON.stringify(exported, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `datalogic-provider-usage-${new Date().toISOString().slice(0, 10)}.json`;
      anchor.click();
      URL.revokeObjectURL(url);
      toast('Redacted provider usage ledger exported.', 'success');
    } catch (error) {
      toast(`Failed to export provider usage: ${formatError(error)}`, 'error');
    }
  };

  const handleResetLedger = async () => {
    if (!window.confirm('Reset the local provider usage and privacy ledger? This cannot be undone.')) return;
    setResettingLedger(true);
    try {
      await request('/gateway/usage-ledger', {
        method: 'DELETE',
        body: JSON.stringify({ confirmation: 'RESET_PROVIDER_USAGE_LEDGER' }),
      });
      await loadUsageLedger();
      toast('Provider usage ledger reset.', 'success');
    } catch (error) {
      toast(`Failed to reset provider usage: ${formatError(error)}`, 'error');
    } finally {
      setResettingLedger(false);
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
    <div className="space-y-6" aria-busy={loading || saving || testing || savingPrefs || loadingLedger || resettingLedger}>
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
              const status = getProviderStatus(entry, Boolean(verifiedProviders[entry.type]));
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
                  <Badge variant={status.variant}>
                    {status.label}
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
                  value={effectiveModel}
                  onChange={(event: React.ChangeEvent<HTMLSelectElement>) => setModel(event.target.value)}
                >
                  {modelOptions.length === 0 && <option value={effectiveModel}>{effectiveModel}</option>}
                  {modelOptions.map((entry) => (
                    <option key={entry} value={entry}>{entry}</option>
                  ))}
                </Select>
                {reasoningEffort && (
                  <p className="text-xs text-muted-foreground">
                    Reasoning level: <span className="font-medium capitalize">{reasoningEffort}</span> (default)
                  </p>
                )}
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

            {selectedProvider?.has_api_key && isConfigurableProviderType(selectedProvider.type) && (
              <div
                className={`rounded-md border px-3 py-2 text-sm flex items-center gap-2 ${
                  selectedProviderVerified
                    ? 'border-green-500/30 bg-green-500/10 text-green-700 dark:text-green-300'
                    : 'border-blue-500/30 bg-blue-500/10 text-blue-700 dark:text-blue-300'
                }`}
                role="status"
                aria-live="polite"
              >
                {selectedProviderVerified && <CheckCircle2 className="h-4 w-4" />}
                {selectedProviderVerified
                  ? `${selectedProvider.type} is available for the selected model.`
                  : `${selectedProvider.type} credentials are stored. Use Test Model to validate availability.`}
              </div>
            )}

            {selectedProvider && !isConfigurableProviderType(selectedProvider.type) && (
              <div className="rounded-md border border-yellow-500/30 bg-yellow-500/10 px-3 py-2 text-sm text-yellow-700 dark:text-yellow-300" role="status" aria-live="polite">
                `{selectedProvider.type}` is a legacy provider row and is not available for the current active cloud model configuration.
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <ShieldCheck className="h-4 w-4" />
            Provider Usage and Privacy Ledger
          </CardTitle>
          <CardDescription>
            Review server-enforced call/token ceilings and content-free external-provider egress records. Prompts, responses, and credentials are never stored in this ledger.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!usageLedger && !loadingLedger && (
            <p className="text-sm text-muted-foreground">Usage ledger is unavailable. Provider calls fail closed when budget accounting cannot be read.</p>
          )}
          {usageLedger && (
            <>
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <div className="rounded-lg border p-3">
                  <p className="text-xs text-muted-foreground">Calls today</p>
                  <p className="text-lg font-semibold">{formatCount(usageLedger.daily.calls)} / {formatCount(usageLedger.limits.daily_calls)}</p>
                  <p className="text-xs text-muted-foreground">{formatCount(usageLedger.remaining.daily_calls)} remaining</p>
                </div>
                <div className="rounded-lg border p-3">
                  <p className="text-xs text-muted-foreground">Tokens this month</p>
                  <p className="text-lg font-semibold">{formatCount(usageLedger.monthly.tokens_total)} / {formatCount(usageLedger.limits.monthly_tokens)}</p>
                  <p className="text-xs text-muted-foreground">{formatCount(usageLedger.remaining.monthly_tokens)} remaining</p>
                </div>
                <div className="rounded-lg border p-3">
                  <p className="text-xs text-muted-foreground">Estimated spend this month</p>
                  <p className="text-lg font-semibold">
                    {usageLedger.monthly.known_estimated_cost_usd === null
                      ? 'Unknown'
                      : `$${usageLedger.monthly.known_estimated_cost_usd.toFixed(4)}`}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {usageLedger.limits.monthly_spend_usd === null
                      ? 'No owner ceiling configured'
                      : `$${usageLedger.limits.monthly_spend_usd.toFixed(2)} ceiling`}
                  </p>
                </div>
                <div className="rounded-lg border p-3">
                  <p className="text-xs text-muted-foreground">Pricing coverage</p>
                  <p className="text-lg font-semibold capitalize">{usageLedger.pricing_status}</p>
                  <p className="text-xs text-muted-foreground">{formatCount(usageLedger.monthly.unknown_price_calls)} calls with unknown price</p>
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="text-sm font-semibold">Recent external disclosures</h3>
                {usageLedger.entries.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No provider calls are recorded for this period.</p>
                ) : (
                  <div className="space-y-2">
                    {usageLedger.entries.slice(0, 5).map((entry) => (
                      <div key={entry.id} className="rounded-lg border p-3 text-xs">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="font-semibold">{entry.provider} / {entry.model || 'unknown model'}</span>
                          <Badge variant="outline">{entry.status}</Badge>
                        </div>
                        <p className="mt-1 text-muted-foreground">
                          Purpose: {entry.purpose}. Disclosed categories: {entry.disclosed_categories.join(', ') || 'none recorded'}.
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}

          <div className="flex flex-wrap gap-2">
            <Button variant="outline" size="sm" onClick={() => void loadUsageLedger()} disabled={loadingLedger} aria-label="Refresh provider usage ledger">
              <RefreshCw className={`h-3.5 w-3.5 mr-1.5 ${loadingLedger ? 'animate-spin' : ''}`} /> Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={() => void handleExportLedger()} aria-label="Export provider usage ledger">
              <Download className="h-3.5 w-3.5 mr-1.5" /> Export redacted JSON
            </Button>
            <Button variant="outline" size="sm" onClick={() => void handleResetLedger()} disabled={resettingLedger} aria-label="Reset provider usage ledger">
              <Trash2 className="h-3.5 w-3.5 mr-1.5" /> {resettingLedger ? 'Resetting...' : 'Reset ledger'}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default AiModelSettings;

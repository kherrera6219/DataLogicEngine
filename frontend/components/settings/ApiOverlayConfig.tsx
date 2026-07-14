'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Card, CardContent, CardHeader, CardTitle
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select } from "@/components/ui/select";
import { useToast } from "@/components/ui/use-toast";
import {
  BarChart3, Terminal, Play, Copy, RefreshCw, Eye, Shield
} from "lucide-react";
import {
  BarChart, Bar, XAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { api, ApiError, buildApiUrl, request } from '@/lib/api';

interface TestResult {
  confidence: number | null;
  answer: string;
  trace: {
    runId: string;
    provider: string;
    model: string;
  };
}

interface ProviderOption {
  id?: string;
  name: string;
  type: string;
  model?: string;
  is_default?: boolean;
}

interface ActivityPoint {
  name: string;
  queries: number;
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

const PROVIDER_MODELS: Record<string, string[]> = {
  openai: ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'],
  anthropic: ['claude-opus-4-7', 'claude-sonnet-4-6', 'claude-haiku-4-5'],
  google: ['gemini-3.1-pro-preview', 'gemini-3-flash-preview'],
  azure: ['gpt-5.5', 'gpt-5.4'],
};

function formatDayLabel(date: Date): string {
  return date.toLocaleDateString(undefined, { weekday: 'short' });
}

function buildLast7DaySeries(timestamps: string[]): ActivityPoint[] {
  const days: Date[] = [];
  for (let i = 6; i >= 0; i -= 1) {
    const day = new Date();
    day.setHours(0, 0, 0, 0);
    day.setDate(day.getDate() - i);
    days.push(day);
  }

  const counts = new Map<string, number>();
  for (const day of days) {
    counts.set(day.toISOString().slice(0, 10), 0);
  }

  for (const raw of timestamps) {
    const parsed = new Date(raw);
    if (Number.isNaN(parsed.getTime())) continue;
    const key = new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate()).toISOString().slice(0, 10);
    if (!counts.has(key)) continue;
    counts.set(key, (counts.get(key) || 0) + 1);
  }

  return days.map((day) => {
    const key = day.toISOString().slice(0, 10);
    return { name: formatDayLabel(day), queries: counts.get(key) || 0 };
  });
}

function formatRequestError(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

/** Maps HTTP status codes from the provider-test endpoint to user-actionable labels. */
interface ProviderTestError {
  message: string;
  statusCode?: number;
}

function mapProviderTestError(error: unknown): ProviderTestError {
  if (error instanceof ApiError) {
    const detail = error.message;
    const statusCode = error.status;
    let message = detail;
    
    switch (statusCode) {
      case 401:
        message = `Invalid API key — ${detail}`;
        break;
      case 429:
        message = `Rate limited — ${detail}`;
        break;
      case 422:
        message = `Invalid model — ${detail}`;
        break;
      case 504:
        message = `Network error — ${detail}`;
        break;
    }
    
    return { message, statusCode };
  }
  return { message: formatRequestError(error) };
}

export function ApiOverlayConfig() {
  const { toast } = useToast();
  const [provider, setProvider] = useState("openai");
  const [model, setModel] = useState("gpt-5.5");
  const [apiKey, setApiKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');

  const [tier, setTier] = useState("moderate");
  const [confidence, setConfidence] = useState(99.5);

  const [testQuery, setTestQuery] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [testResult, setTestResult] = useState<TestResult | null>(null);
  const [testConnectionStatusCode, setTestConnectionStatusCode] = useState<number | null>(null);
  const [testConnectionErrorMessage, setTestConnectionErrorMessage] = useState<string>("");
  const [activeTab, setActiveTab] = useState("python");

  const [providers, setProviders] = useState<ProviderOption[]>([]);
  const [selectedProviderId, setSelectedProviderId] = useState<string | null>(null);
  const [activityData, setActivityData] = useState<ActivityPoint[]>([]);
  const [activeProvidersCount, setActiveProvidersCount] = useState(0);
  const [complianceScore, setComplianceScore] = useState('N/A');

  useEffect(() => {
    let cancelled = false;
    async function loadData() {
      try {
        const [providerData, activity, health, overview] = await Promise.all([
          request<{ providers?: ProviderOption[] }>('/gateway/providers').catch(() => ({ providers: [] })),
          api.analytics.activity(100).catch(() => []),
          api.chat.getHealth().catch(() => ({ active_providers: 0, message: 'Unavailable' })),
          request<{ compliance_score?: string | number }>('/analytics/overview').catch(() => ({ compliance_score: undefined })),
        ]);

        if (cancelled) return;

        const availableProviders = providerData.providers || [];
        setProviders(availableProviders);
        setActiveProvidersCount(health.active_providers || 0);
        if (overview?.compliance_score) {
          setComplianceScore(String(overview.compliance_score));
        }

        if (availableProviders.length > 0) {
          const preferred = availableProviders.find((entry) => entry.is_default) || availableProviders[0];
          const nextProvider = preferred.type || preferred.name || 'openai';
          setProvider(nextProvider.toLowerCase());
          setSelectedProviderId(preferred.id || null);
          if (preferred.model) {
            setModel(preferred.model);
          }
        }

        const activityEntries = Array.isArray(activity) ? (activity as Array<{ time?: string }>) : [];
        const timestamps = activityEntries
          .map((entry) => entry.time)
          .filter((value): value is string => Boolean(value));
        setActivityData(buildLast7DaySeries(timestamps));
      } catch {
        if (!cancelled) {
          setActivityData(buildLast7DaySeries([]));
        }
      }
    }

    void loadData();
    return () => {
      cancelled = true;
    };
  }, []);

  const modelOptions = useMemo(() => {
    const normalized = provider.toLowerCase();
    const fromProvider = providers
      .filter((entry) => (entry.type || entry.name || '').toLowerCase() === normalized)
      .map((entry) => entry.model)
      .filter((entry): entry is string => Boolean(entry));
    const defaults = PROVIDER_MODELS[normalized] || [];
    return Array.from(new Set([...fromProvider, ...defaults]));
  }, [provider, providers]);

  // Sync model to available options during render instead of via effect.
  const effectiveModel = useMemo(() => {
    if (!modelOptions.length) return model;
    return modelOptions.includes(model) ? model : modelOptions[0];
  }, [model, modelOptions]);

  // Keep model state in sync when effectiveModel diverges.
  if (effectiveModel !== model) {
    setModel(effectiveModel);
  }

  // Derive selectedProviderId from provider + providers list (no effect needed).
  const derivedProviderId = useMemo(() => {
    const normalized = provider.toLowerCase();
    const matchingProvider = providers.find(
      (entry) => (entry.type || entry.name || '').toLowerCase() === normalized
    );
    return matchingProvider?.id || null;
  }, [provider, providers]);

  // Keep selectedProviderId in sync when the derivation changes.
  if (derivedProviderId !== selectedProviderId) {
    setSelectedProviderId(derivedProviderId);
  }

  // Reset save/connection status when inputs change.
  const isInitialMount = useRef(true);
  useEffect(() => {
    if (isInitialMount.current) {
      isInitialMount.current = false;
      return;
    }
    setSaveStatus('idle');
    setConnectionStatus('idle');
  }, [apiKey, model, provider]);

  const totalQueries = activityData.reduce((sum, point) => sum + point.queries, 0);
  const gatewayChatEndpoint = useMemo(() => buildApiUrl('/gateway/chat'), []);

  const handleSaveKey = async (): Promise<string | null> => {
    if (!apiKey.trim()) {
      toast("Enter an API key before saving.", "warning");
      return null;
    }

    setSaveStatus('saving');
    try {
      const result = await request<SaveKeyResponse>('/gateway/keys', {
        method: 'POST',
        body: JSON.stringify({
          provider,
          key: apiKey.trim(),
          model,
        }),
      });

      const savedProvider = result?.provider;
      const savedId = savedProvider?.id || null;
      const savedProviderType = String(
        savedProvider?.provider_type || savedProvider?.type || provider
      ).toLowerCase();

      setProviders((previous) => {
        const next = [...previous];
        const existingIndex = next.findIndex(
          (entry) => (entry.type || entry.name || '').toLowerCase() === savedProviderType
        );

        const nextEntry: ProviderOption = {
          id: savedId || undefined,
          name: savedProvider?.name || savedProviderType,
          type: savedProviderType,
          model,
        };

        if (existingIndex >= 0) {
          next[existingIndex] = {
            ...next[existingIndex],
            ...nextEntry,
          };
        } else {
          next.push(nextEntry);
        }
        return next;
      });

      if (savedId) {
        setSelectedProviderId(savedId);
      }

      setSaveStatus('saved');
      toast("API key saved.", "success");
      return savedId;
    } catch (error) {
      setSaveStatus('error');
      toast(`Failed to save provider key: ${formatRequestError(error)}`, "error");
      return null;
    }
  };

  const handleTestConnection = async () => {
    setConnectionStatus('testing');
    setTestConnectionStatusCode(null);
    setTestConnectionErrorMessage("");
    const providerId = selectedProviderId || await handleSaveKey();
    if (!providerId) {
      setConnectionStatus('error');
      return;
    }

    try {
      const result = await request<{ success?: boolean; message?: string; error?: string }>(
        `/gateway/providers/${providerId}/test`,
        { method: 'POST' }
      );
      if (!result?.success) {
        throw new Error(result?.error || result?.message || 'Provider connection test failed.');
      }
      setConnectionStatus('success');
      setSaveStatus('saved');
      setTestConnectionStatusCode(null);
      setTestConnectionErrorMessage("");
      toast(result.message || "Provider connection successful.", "success");
    } catch (error) {
      setConnectionStatus('error');
      const { message, statusCode } = mapProviderTestError(error);
      setTestConnectionStatusCode(statusCode || null);
      setTestConnectionErrorMessage(message);
      toast(message, "error");
    }
  };

  const handleRunTest = async () => {
    if (!testQuery.trim()) return;
    setIsProcessing(true);
    setTestResult(null);
    try {
      const result = await request<{
        response?: string;
        run_id?: string;
        provider_used?: string;
        model_used?: string;
        confidence_score?: number | null;
      }>('/gateway/chat', {
        method: 'POST',
        body: JSON.stringify({
          messages: [{ role: 'user', content: testQuery }],
          provider,
          model,
          mode: 'chat',
          run_ukg_pipeline: true,
        }),
      });

      setTestResult({
        confidence: result.confidence_score ?? null,
        answer: result.response || 'No response body returned by gateway.',
        trace: {
          runId: result.run_id || 'n/a',
          provider: result.provider_used || provider,
          model: result.model_used || model,
        },
      });
      toast("Gateway query executed.", "success", 2000);
    } catch (error) {
      toast(`Gateway query failed: ${formatRequestError(error)}`, "error");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-500" aria-busy={saveStatus === 'saving' || connectionStatus === 'testing' || isProcessing}>
      <section className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <Card className="glass-card border-white/10 bg-gradient-to-br from-blue-900/20 to-purple-900/20 col-span-1 lg:col-span-4 p-6 flex flex-col md:flex-row justify-between items-center text-center md:text-left">
          <div>
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
              UKG API Overlay Configuration
            </h1>
            <p className="text-muted-foreground mt-1">
              Live provider and gateway controls.
            </p>
          </div>
          <div className="flex gap-4 mt-4 md:mt-0">
            <div className="text-center p-3 bg-white/5 rounded-lg border border-white/5">
              <div className="text-xs text-gray-400 uppercase tracking-widest">Queries</div>
              <div className="text-xl font-bold text-white">{totalQueries}</div>
            </div>
            <div className="text-center p-3 bg-white/5 rounded-lg border border-white/5">
              <div className="text-xs text-gray-400 uppercase tracking-widest">Valid</div>
              <div className="text-xl font-bold text-green-400">{complianceScore}</div>
            </div>
            <div className="text-center p-3 bg-white/5 rounded-lg border border-white/5 hidden md:block">
              <div className="text-xs text-gray-400 uppercase tracking-widest">Providers</div>
              <div className="text-xl font-bold text-blue-400">{activeProvidersCount}</div>
            </div>
          </div>
        </Card>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <Card className="border-white/10 space-y-4">
            <CardHeader className="bg-white/5 border-b border-white/5 pb-4">
              <div className="flex justify-between items-center">
                <CardTitle className="text-lg flex items-center gap-2">
                  <span className="bg-blue-600 w-6 h-6 rounded-full text-xs flex items-center justify-center text-white">1</span>
                  Configure LLM Provider
                </CardTitle>
                {connectionStatus === 'success' && <Badge variant="success" className="bg-green-500/20 text-green-400 border-green-500/50">Verified</Badge>}
                {connectionStatus !== 'success' && saveStatus === 'saved' && <Badge variant="outline" className="border-blue-500/50 text-blue-300">Saved</Badge>}
              </div>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label htmlFor="api-overlay-provider" className="text-xs font-bold uppercase text-gray-500">Provider</label>
                  <Select id="api-overlay-provider" value={provider} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setProvider(e.target.value)} className="bg-white/5 border-white/10">
                    {Array.from(new Set([
                      ...providers.map((entry) => (entry.type || entry.name || '').toLowerCase()),
                      'openai',
                      'anthropic',
                      'google',
                      'azure',
                    ].filter(Boolean))).map((entry) => (
                      <option key={entry} value={entry}>{entry}</option>
                    ))}
                  </Select>
                </div>
                <div className="space-y-2">
                  <label htmlFor="api-overlay-model" className="text-xs font-bold uppercase text-gray-500">Model</label>
                  <Select id="api-overlay-model" value={model} onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setModel(e.target.value)} className="bg-white/5 border-white/10">
                    {modelOptions.length === 0 && <option value={model}>{model}</option>}
                    {modelOptions.map((entry) => (
                      <option key={entry} value={entry}>{entry}</option>
                    ))}
                  </Select>
                </div>
              </div>

              {(
                <div className="space-y-2">
                  <label htmlFor="api-overlay-api-key" className="text-xs font-bold uppercase text-gray-500">API Key</label>
                  <div className="flex gap-2 flex-wrap">
                    <div className="relative flex-1">
                      <Input
                        id="api-overlay-api-key"
                        type={showKey ? "text" : "password"}
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="sk-..."
                        className="bg-white/5 border-white/10 pr-10 font-mono"
                      />
                      <button
                        onClick={() => setShowKey(!showKey)}
                        className="absolute right-3 top-2.5 text-gray-400 hover:text-white"
                        type="button"
                        aria-label={showKey ? "Hide API key" : "Show API key"}
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                    </div>
                    <Button
                      variant={saveStatus === 'saved' ? 'secondary' : 'default'}
                      onClick={handleSaveKey}
                      disabled={saveStatus === 'saving' || !apiKey.trim()}
                      className="w-32"
                      aria-label="Save provider key"
                    >
                      {saveStatus === 'saving' ? 'Saving...' : saveStatus === 'saved' ? 'Saved' : 'Save Key'}
                    </Button>
                    <Button
                      variant={connectionStatus === 'success' ? 'secondary' : 'outline'}
                      onClick={handleTestConnection}
                      disabled={connectionStatus === 'testing' || !apiKey.trim()}
                      className="w-40"
                      aria-label="Test provider connection"
                    >
                      {connectionStatus === 'testing' ? 'Testing...' : connectionStatus === 'success' ? 'Connected' : 'Test Connection'}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-white/10">
            <CardHeader className="bg-white/5 border-b border-white/5 pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <span className="bg-purple-600 w-6 h-6 rounded-full text-xs flex items-center justify-center text-white">2</span>
                Configure Enhancement Layer
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              <div className="space-y-3">
                <label className="text-xs font-bold uppercase text-gray-500">Processing Tier</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {[
                    { id: 'trivial', name: 'Trivial', desc: 'Direct retrieval' },
                    { id: 'moderate', name: 'Moderate', desc: 'Retrieval + reasoning' },
                    { id: 'high', name: 'High-Stakes', desc: 'Deep validation chain' },
                    { id: 'extreme', name: 'Extreme', desc: 'Extended simulation pass' },
                  ].map((entry) => (
                    <button
                      type="button"
                      key={entry.id}
                      onClick={() => setTier(entry.id)}
                      aria-pressed={tier === entry.id}
                      aria-label={`Processing tier ${entry.name}`}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${tier === entry.id ? 'bg-purple-500/20 border-purple-500 ring-1 ring-purple-500' : 'bg-white/5 border-white/10 hover:border-white/30'}`}
                    >
                      <div className="font-bold text-sm mb-1">{entry.name}</div>
                      <div className="text-xs text-muted-foreground">{entry.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-4 pt-4 border-t border-white/5">
                <div className="flex justify-between">
                  <label className="text-xs font-bold uppercase text-gray-500">Confidence Threshold</label>
                  <span className="text-sm font-mono font-bold text-purple-400">{confidence}%</span>
                </div>
                <input
                  type="range"
                  min="90"
                  max="99.9"
                  step="0.1"
                  value={confidence}
                  onChange={(e) => setConfidence(parseFloat(e.target.value))}
                  className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-purple-500"
                  title="Confidence Threshold"
                  aria-label="Confidence threshold"
                />
              </div>
            </CardContent>
          </Card>

          <Card className="border-white/10">
            <CardHeader className="bg-white/5 border-b border-white/5 pb-4">
              <CardTitle className="text-lg flex items-center gap-2">
                <span className="bg-green-600 w-6 h-6 rounded-full text-xs flex items-center justify-center text-white">3</span>
                API Endpoint & Logic Integration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 pt-6">
              <div className="relative">
                <label className="text-xs font-bold uppercase text-gray-500 mb-2 block">Gateway Endpoint</label>
                <div className="flex gap-2">
                  <code className="flex-1 bg-black/40 border border-white/10 p-3 rounded-lg font-mono text-xs text-green-400">
                    {gatewayChatEndpoint}
                  </code>
                  <Button size="icon" variant="outline" title="Copy Endpoint" aria-label="Copy gateway endpoint"><Copy className="h-4 w-4" /></Button>
                </div>
              </div>

              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="bg-white/5 h-10 mb-2">
                  <TabsTrigger value="python">Python</TabsTrigger>
                  <TabsTrigger value="curl">cURL</TabsTrigger>
                  <TabsTrigger value="js">Node.js</TabsTrigger>
                </TabsList>
                <TabsContent value="python">
                  <pre className="bg-black/50 p-4 rounded-lg text-xs font-mono text-gray-300 overflow-x-auto border border-white/10">
{`import requests

response = requests.post(
  "${gatewayChatEndpoint}",
  json={
    "provider": "${provider}",
    "model": "${model}",
    "messages": [{"role": "user", "content": "Analyze compliance posture"}]
  }
)

print(response.json())`}
                  </pre>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <Card className="border-white/10 border-t-4 border-t-purple-500 shadow-2xl">
            <CardHeader>
              <CardTitle className="flex justify-between items-center">
                <span>Testing Playground</span>
                <Terminal className="h-4 w-4 text-purple-500" />
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label htmlFor="test-prompt" className="sr-only">Test Prompt</label>
                <textarea
                  id="test-prompt"
                  value={testQuery}
                  onChange={(e) => setTestQuery(e.target.value)}
                  placeholder="Enter a test prompt to validate your configuration..."
                  className="w-full bg-black/20 border-white/10 rounded-lg p-3 text-sm min-h-[100px] focus:ring-purple-500"
                />
              </div>
              <Button onClick={handleRunTest} disabled={isProcessing || !testQuery} className="w-full bg-purple-600 hover:bg-purple-700" aria-label="Run enhancement test">
                {isProcessing ? <RefreshCw className="h-4 w-4 animate-spin mr-2" /> : <Play className="h-4 w-4 mr-2" />}
                Test Enhancement
              </Button>

              {testResult && (
                <div className="mt-4 p-4 bg-green-900/10 border border-green-500/20 rounded-lg animate-in zoom-in-95">
                  <div className="flex justify-between items-center mb-2">
                    <Badge variant="success" className="bg-green-500/20 text-green-400">
                      {testResult.confidence === null
                        ? 'Confidence not measured'
                        : `${(testResult.confidence * 100).toFixed(1)}% Confidence`}
                    </Badge>
                    <span className="text-[10px] text-gray-500">{testResult.trace.runId}</span>
                  </div>
                  <p className="text-xs text-gray-300 leading-relaxed">
                    {testResult.answer}
                  </p>
                  <div className="mt-3 pt-3 border-t border-white/5 flex gap-2 text-[10px] text-gray-500 font-mono">
                    <span>{testResult.trace.provider}</span>
                    <span>{testResult.trace.model}</span>
                  </div>
                </div>
              )}

              {connectionStatus === 'error' && testConnectionErrorMessage && (
                <div className="mt-4 p-4 bg-red-900/10 border border-red-500/20 rounded-lg animate-in zoom-in-95">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-semibold text-red-300">Connection Error</span>
                    {testConnectionStatusCode && (
                      <Badge variant="destructive" className="bg-red-500/20 text-red-300 border-red-500/50">
                        HTTP {testConnectionStatusCode}
                      </Badge>
                    )}
                  </div>
                  <p className="text-xs text-red-200">
                    {testConnectionErrorMessage}
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-white/10">
            <CardHeader>
              <CardTitle className="flex justify-between items-center text-sm">
                <span>Real-Time Activity</span>
                <BarChart3 className="h-4 w-4 text-gray-500" />
              </CardTitle>
            </CardHeader>
            <CardContent className="h-[200px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={activityData}>
                  <XAxis dataKey="name" stroke="#4b5563" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', fontSize: '12px' }}
                    itemStyle={{ color: '#e5e7eb' }}
                  />
                  <Bar dataKey="queries" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                    {activityData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={index === activityData.length - 1 ? '#8b5cf6' : '#3b82f6'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <Card className="border-white/10">
            <CardHeader>
              <CardTitle className="flex justify-between items-center text-sm">
                <span>Security & Compliance</span>
                <Shield className="h-4 w-4 text-green-500" />
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Configured Providers</span>
                <Badge variant="outline" className="text-[10px]">{providers.length}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Gateway Health</span>
                <Badge variant="outline" className="text-[10px]">{activeProvidersCount > 0 ? 'Provider active' : 'No active provider'}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">Compliance Score</span>
                <span className="text-xs font-mono">{complianceScore}</span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

'use client';

import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import {
  api,
  buildApiUrl,
  ClientKeyCreate,
  ClientKeyMetadata,
  CopyOnceClientKey,
  GatewayAuditEvent,
  GatewayCapabilities,
  GatewayControlPlaneStatus,
  GATEWAY_SCOPES,
  GatewayScope,
} from '@/lib/api';
import { Copy, KeyRound, RefreshCw, ShieldCheck } from 'lucide-react';

type Snapshot = {
  keys: ClientKeyMetadata[];
  capabilities: GatewayCapabilities | null;
  controlPlane: GatewayControlPlaneStatus | null;
  health: Record<string, unknown>;
  usage: Record<string, unknown>;
  jobs: Array<Record<string, unknown>>;
  audit: GatewayAuditEvent[];
};

const EMPTY_SNAPSHOT: Snapshot = {
  keys: [],
  capabilities: null,
  controlPlane: null,
  health: {},
  usage: {},
  jobs: [],
  audit: [],
};

const DEFAULT_SCOPES: GatewayScope[] = [
  'chat',
  'stream',
  'run:create',
  'run:read',
  'run:cancel',
  'models:read',
];

function formatDate(value: string | null | undefined): string {
  if (!value) return 'Never';
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? 'Unknown' : parsed.toLocaleString();
}

function humanize(value: unknown): string {
  return String(value ?? 'unknown').replaceAll('_', ' ');
}

export function ClientGatewayConfig() {
  const { toast } = useToast();
  const [snapshot, setSnapshot] = useState<Snapshot>(EMPTY_SNAPSHOT);
  const [loading, setLoading] = useState(true);
  const [workingId, setWorkingId] = useState<string | null>(null);
  const [copyOnce, setCopyOnce] = useState<CopyOnceClientKey | null>(null);
  const [name, setName] = useState('');
  const [scopes, setScopes] = useState<GatewayScope[]>(DEFAULT_SCOPES);
  const [rpm, setRpm] = useState(60);
  const [daily, setDaily] = useState(1000);
  const [maxTokens, setMaxTokens] = useState(4096);
  const [concurrency, setConcurrency] = useState(2);
  const [expiryDays, setExpiryDays] = useState(90);
  const [activeTab, setActiveTab] = useState('server');

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [keys, capabilities, controlPlane, health, usage, jobs, audit] = await Promise.all([
        api.gateway.clientKeys(),
        api.gateway.capabilities(),
        api.gateway.controlPlaneStatus(),
        api.gateway.health(),
        api.gateway.usage(),
        api.gateway.jobs(),
        api.gateway.clientKeyAudit(),
      ]);
      setSnapshot({
        keys: keys.api_keys,
        capabilities,
        controlPlane,
        health,
        usage,
        jobs: jobs.jobs,
        audit: audit.events,
      });
    } catch (error) {
      toast(`Client Gateway could not be loaded: ${error instanceof Error ? error.message : String(error)}`, 'error');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    const task = window.setTimeout(() => void refresh(), 0);
    return () => window.clearTimeout(task);
  }, [refresh]);

  const createClient = async () => {
    if (!name.trim() || scopes.length === 0) {
      toast('Enter a client name and select at least one permission.', 'warning');
      return;
    }
    const payload: ClientKeyCreate = {
      name: name.trim(),
      scopes,
      rate_limit_rpm: rpm,
      rate_limit_daily: daily,
      max_tokens_per_request: maxTokens,
      max_concurrent_requests: concurrency,
      expires_in_days: expiryDays,
    };
    setWorkingId('create');
    try {
      const created = await api.gateway.createClientKey(payload);
      setCopyOnce(created);
      setName('');
      toast('Client created. Copy its key now; it will not be shown again.', 'success');
      await refresh();
    } catch (error) {
      toast(`Client could not be created: ${error instanceof Error ? error.message : String(error)}`, 'error');
    } finally {
      setWorkingId(null);
    }
  };

  const lifecycleAction = async (
    key: ClientKeyMetadata,
    action: 'rotate' | 'revoke' | 'expire' | 'delete',
  ) => {
    const confirmation = action === 'rotate'
      ? `Rotate ${key.name}? The previous key will remain valid for five minutes.`
      : `${action[0].toUpperCase()}${action.slice(1)} ${key.name}?`;
    if (!window.confirm(confirmation)) return;
    setWorkingId(key.id);
    try {
      if (action === 'rotate') {
        setCopyOnce(await api.gateway.rotateClientKey(key.id, 300));
      } else if (action === 'revoke') {
        await api.gateway.revokeClientKey(key.id, 'owner_revoked_from_desktop');
      } else if (action === 'expire') {
        await api.gateway.expireClientKey(key.id, 'owner_expired_from_desktop');
      } else {
        await api.gateway.deleteClientKey(key.id);
      }
      toast(`Client key ${action} completed.`, 'success');
      await refresh();
    } catch (error) {
      toast(`Client key action failed: ${error instanceof Error ? error.message : String(error)}`, 'error');
    } finally {
      setWorkingId(null);
    }
  };

  const copySecret = async () => {
    if (!copyOnce) return;
    await navigator.clipboard.writeText(copyOnce.api_key);
    toast('Client key copied.', 'success');
  };

  const nativeEndpoint = useMemo(() => buildApiUrl('/gateway/chat'), []);
  const example = useMemo(() => `Invoke-RestMethod -Method Post -Uri "${nativeEndpoint}" \`
  -Headers @{ Authorization = "Bearer ukg_REPLACE_WITH_COPY_ONCE_KEY" } \`
  -ContentType "application/json" \`
  -Body '{"virtual_model":"dle-standard","messages":[{"role":"user","content":"Hello"}],"idempotency_key":"replace-with-unique-id"}'`, [nativeEndpoint]);

  const month = (snapshot.usage.monthly || {}) as Record<string, unknown>;
  const profile = snapshot.controlPlane?.profile || snapshot.capabilities?.profile || 'unknown';

  return (
    <div className="space-y-6" aria-busy={loading || Boolean(workingId)}>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold">Client Gateway</h2>
          <p className="text-sm text-muted-foreground">Inbound access for approved applications. Provider keys stay in Provider Connections.</p>
        </div>
        <Button variant="outline" onClick={() => void refresh()} disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </Button>
      </div>

      {copyOnce && (
        <Card className="border-amber-500/50 bg-amber-500/10" role="alert">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><KeyRound className="h-5 w-5" /> Copy this client key now</CardTitle>
            <CardDescription>This is the only time the full key is available.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3 sm:flex-row">
            <code className="min-w-0 flex-1 overflow-x-auto rounded bg-black/30 p-3 text-xs">{copyOnce.api_key}</code>
            <Button onClick={() => void copySecret()}><Copy className="mr-2 h-4 w-4" /> Copy key</Button>
            <Button variant="outline" onClick={() => setCopyOnce(null)}>I saved it</Button>
          </CardContent>
        </Card>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="flex h-auto flex-wrap justify-start">
          {['server', 'clients', 'models', 'policies', 'usage', 'audit', 'health', 'examples'].map((tab) => (
            <TabsTrigger key={tab} value={tab}>{tab === 'models' ? 'Virtual Models & Routing' : tab[0].toUpperCase() + tab.slice(1)}</TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="server" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card><CardHeader><CardDescription>Listener profile</CardDescription><CardTitle>{humanize(profile)}</CardTitle></CardHeader></Card>
            <Card><CardHeader><CardDescription>Bind addresses</CardDescription><CardTitle className="text-base">{snapshot.controlPlane?.bind_addresses.join(', ') || 'Unknown'}</CardTitle></CardHeader></Card>
            <Card><CardHeader><CardDescription>TLS</CardDescription><CardTitle className="text-base">{humanize(snapshot.controlPlane?.tls.state)}</CardTitle></CardHeader></Card>
            <Card><CardHeader><CardDescription>Firewall</CardDescription><CardTitle className="text-base">{humanize(snapshot.controlPlane?.firewall.state)}</CardTitle></CardHeader></Card>
          </div>
          <Card>
            <CardHeader><CardTitle>Private Windows gateway</CardTitle></CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">Private access is disabled. It cannot be enabled until TLS, certificate, firewall, security, and two-machine qualification pass.</p>
              <Button className="mt-4" disabled>Private gateway not qualified</Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="clients" className="space-y-4">
          <Card>
            <CardHeader><CardTitle>Create API client</CardTitle><CardDescription>The full client key is returned once.</CardDescription></CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              <label className="space-y-1"><span className="text-sm">Client name</span><Input aria-label="Client name" value={name} onChange={(event) => setName(event.target.value)} /></label>
              <label className="space-y-1"><span className="text-sm">Expires after days</span><Input aria-label="Expires after days" type="number" min={1} value={expiryDays} onChange={(event) => setExpiryDays(Number(event.target.value))} /></label>
              <div className="flex items-end"><Button onClick={() => void createClient()} disabled={workingId === 'create'}>{workingId === 'create' ? 'Creating…' : 'Create client'}</Button></div>
            </CardContent>
          </Card>
          <div className="space-y-3">
            {snapshot.keys.map((key) => (
              <Card key={key.id}>
                <CardContent className="flex flex-col gap-4 pt-6 lg:flex-row lg:items-center lg:justify-between">
                  <div>
                    <div className="flex items-center gap-2"><span className="font-semibold">{key.name}</span><Badge variant={key.is_active ? 'default' : 'outline'}>{key.is_active ? 'Active' : 'Inactive'}</Badge></div>
                    <p className="mt-1 font-mono text-xs text-muted-foreground">{key.key_prefix}… · {key.scopes.join(', ')}</p>
                    <p className="text-xs text-muted-foreground">Requests: {key.total_requests} · Last used: {formatDate(key.last_used_at)} · Expires: {formatDate(key.expires_at)}</p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button size="sm" variant="outline" disabled={!key.is_active || workingId === key.id} onClick={() => void lifecycleAction(key, 'rotate')}>Rotate</Button>
                    <Button size="sm" variant="outline" disabled={!key.is_active || workingId === key.id} onClick={() => void lifecycleAction(key, 'expire')}>Expire</Button>
                    <Button size="sm" variant="destructive" disabled={!key.is_active || workingId === key.id} onClick={() => void lifecycleAction(key, 'revoke')}>Revoke</Button>
                    <Button size="sm" variant="outline" disabled={key.is_active || workingId === key.id} onClick={() => void lifecycleAction(key, 'delete')}>Delete material</Button>
                  </div>
                </CardContent>
              </Card>
            ))}
            {!loading && snapshot.keys.length === 0 && <p className="text-sm text-muted-foreground">No client applications have been approved.</p>}
          </div>
        </TabsContent>

        <TabsContent value="models" className="grid gap-4 md:grid-cols-3">
          {Object.entries(snapshot.capabilities?.virtual_models || {}).map(([id, model]) => (
            <Card key={id}><CardHeader><CardTitle>{id}</CardTitle><CardDescription>{model.description || 'Server-owned governed route'}</CardDescription></CardHeader><CardContent className="text-sm">Mode: {humanize(model.mode)}<br />Provider-call ceiling: {model.max_provider_calls ?? 'Unknown'}</CardContent></Card>
          ))}
        </TabsContent>

        <TabsContent value="policies" className="space-y-4">
          <Card><CardHeader><CardTitle>Default policy for new clients</CardTitle><CardDescription>These limits are enforced by the backend and stored with the client.</CardDescription></CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <label className="space-y-1"><span className="text-sm">Requests per minute</span><Input aria-label="Requests per minute" type="number" min={1} value={rpm} onChange={(event) => setRpm(Number(event.target.value))} /></label>
              <label className="space-y-1"><span className="text-sm">Requests per day</span><Input aria-label="Requests per day" type="number" min={1} value={daily} onChange={(event) => setDaily(Number(event.target.value))} /></label>
              <label className="space-y-1"><span className="text-sm">Tokens per request</span><Input aria-label="Tokens per request" type="number" min={1} value={maxTokens} onChange={(event) => setMaxTokens(Number(event.target.value))} /></label>
              <label className="space-y-1"><span className="text-sm">Concurrent requests</span><Input aria-label="Concurrent requests" type="number" min={1} max={100} value={concurrency} onChange={(event) => setConcurrency(Number(event.target.value))} /></label>
            </CardContent>
          </Card>
          <Card><CardHeader><CardTitle>Permissions for the next client</CardTitle></CardHeader><CardContent className="grid gap-2 md:grid-cols-3">
            {GATEWAY_SCOPES.map((scope) => <label key={scope} className="flex items-center gap-2 rounded border p-2 text-sm"><input type="checkbox" checked={scopes.includes(scope)} onChange={(event) => setScopes((current) => event.target.checked ? [...current, scope] : current.filter((item) => item !== scope))} />{scope}</label>)}
          </CardContent></Card>
        </TabsContent>

        <TabsContent value="usage" className="grid gap-4 md:grid-cols-3">
          <Card><CardHeader><CardDescription>Calls this month</CardDescription><CardTitle>{String(month.calls ?? 0)}</CardTitle></CardHeader></Card>
          <Card><CardHeader><CardDescription>Input tokens</CardDescription><CardTitle>{String(month.tokens_in ?? 0)}</CardTitle></CardHeader></Card>
          <Card><CardHeader><CardDescription>Output tokens</CardDescription><CardTitle>{String(month.tokens_out ?? 0)}</CardTitle></CardHeader></Card>
          <Card className="md:col-span-3"><CardHeader><CardTitle>Durable jobs</CardTitle><CardDescription>{snapshot.jobs.length} recent jobs are visible in this owner session.</CardDescription></CardHeader></Card>
        </TabsContent>

        <TabsContent value="audit" className="space-y-2">
          {snapshot.audit.map((event) => <Card key={event.id}><CardContent className="flex flex-col gap-1 pt-5 sm:flex-row sm:justify-between"><span className="font-medium">{humanize(event.action)}</span><span className="text-xs text-muted-foreground">{formatDate(event.timestamp)}</span></CardContent></Card>)}
          {!loading && snapshot.audit.length === 0 && <p className="text-sm text-muted-foreground">No client-key lifecycle events recorded.</p>}
        </TabsContent>

        <TabsContent value="health" className="space-y-4">
          <Card><CardHeader><CardTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5" /> Gateway health: {humanize(snapshot.health.status)}</CardTitle><CardDescription>Capability-only check; it does not spend provider tokens.</CardDescription></CardHeader></Card>
          <div className="grid gap-4 md:grid-cols-3">{Object.entries(snapshot.controlPlane?.dependencies || {}).map(([name, state]) => <Card key={name}><CardHeader><CardDescription>{name}</CardDescription><CardTitle className="text-base">{humanize(state.state)}</CardTitle></CardHeader></Card>)}</div>
        </TabsContent>

        <TabsContent value="examples" className="space-y-4">
          <Card><CardHeader><CardTitle>PowerShell</CardTitle><CardDescription>Replace the placeholder with a copy-once DataLogicEngine client key.</CardDescription></CardHeader><CardContent><pre className="overflow-x-auto rounded bg-black/30 p-4 text-xs">{example}</pre></CardContent></Card>
          <Card><CardHeader><CardTitle>Supported clients</CardTitle></CardHeader><CardContent className="text-sm text-muted-foreground">Python and TypeScript SDKs support chat, live governed SSE, durable runs, result polling, cancellation, capability discovery, safe retry, idempotency, and typed errors. The bounded OpenAI facade is available at <code>/v1/chat/completions</code>.</CardContent></Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

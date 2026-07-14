'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { Box, Pause, Play, Plus, RefreshCw, RotateCw, ShieldCheck, ShieldOff, Trash2 } from 'lucide-react';
import { mcp, MCPServer, MCPServerRegistration } from '@/lib/api/mcp';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useToast } from '@/components/ui/use-toast';

const DEFAULT_LIMITS = {
  request_timeout_seconds: 30,
  max_message_bytes: 65_536,
  max_stderr_bytes: 16_384,
  max_process_memory_mb: 256,
};

function commandPreview(server: MCPServer): string {
  return [server.config.command, ...server.config.args].map((part) => part.includes(' ') ? `"${part}"` : part).join(' ');
}

function qualificationLabel(value: string): string {
  return value.replaceAll('_', ' ');
}

export default function MCPServersPage() {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState('');
  const [error, setError] = useState('');
  const [addOpen, setAddOpen] = useState(false);
  const [reviewServer, setReviewServer] = useState<MCPServer | null>(null);
  const [approvedScopes, setApprovedScopes] = useState<string[]>([]);
  const [adding, setAdding] = useState(false);
  const [name, setName] = useState('');
  const [version, setVersion] = useState('1.0.0');
  const [description, setDescription] = useState('');
  const [command, setCommand] = useState('');
  const [argsText, setArgsText] = useState('');
  const [cwd, setCwd] = useState('');
  const [fileRoot, setFileRoot] = useState('');
  const [allowWrite, setAllowWrite] = useState(false);
  const [credentialEnv, setCredentialEnv] = useState('');
  const [credentialRef, setCredentialRef] = useState('');
  const [credentialValue, setCredentialValue] = useState('');
  const { toast } = useToast();

  const fetchServers = useCallback(async () => {
    setError('');
    try {
      const data = await mcp.getServers();
      setServers(data.servers);
    } catch (err) {
      console.error(err);
      setError('Connector status could not be loaded.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function loadServers() {
      if (!cancelled) await fetchServers();
    }
    void loadServers();
    return () => { cancelled = true; };
  }, [fetchServers]);

  const resetForm = () => {
    setName('');
    setVersion('1.0.0');
    setDescription('');
    setCommand('');
    setArgsText('');
    setCwd('');
    setFileRoot('');
    setAllowWrite(false);
    setCredentialEnv('');
    setCredentialRef('');
    setCredentialValue('');
  };

  const handleAddServer = async () => {
    if (!name.trim() || !command.trim() || !cwd.trim() || !fileRoot.trim()) {
      toast('Name, executable, working folder, and approved folder are required.', 'error');
      return;
    }
    const connectorName = name.trim();
    const scopes = [`connector:${connectorName.toLowerCase()}:read`];
    if (allowWrite) scopes.push(`connector:${connectorName.toLowerCase()}:write`);
    const credential_env: Record<string, string> = {};
    const credentials: Record<string, string> = {};
    if (credentialEnv.trim() || credentialRef.trim() || credentialValue) {
      if (!credentialEnv.trim() || !credentialRef.trim() || !credentialValue) {
        toast('Complete all three protected credential fields or leave them blank.', 'error');
        return;
      }
      credential_env[credentialEnv.trim()] = credentialRef.trim();
      credentials[credentialRef.trim()] = credentialValue;
    }
    const registration: MCPServerRegistration = {
      name: connectorName,
      version: version.trim() || '1.0.0',
      description: description.trim(),
      config: {
        transport: 'stdio',
        protocol_version: '2025-11-25',
        command: command.trim(),
        args: argsText.split('\n').map((value) => value.trim()).filter(Boolean),
        cwd: cwd.trim(),
        env: {},
        credential_env,
        file_roots: [fileRoot.trim()],
        network_destinations: [],
        requested_scopes: scopes,
        limits: DEFAULT_LIMITS,
      },
      ...(Object.keys(credentials).length ? { credentials } : {}),
    };
    setAdding(true);
    try {
      const created = await mcp.createServer(registration);
      setAddOpen(false);
      resetForm();
      setReviewServer(created);
      setApprovedScopes(created.requested_scopes);
      toast('Connector registered but not started. Review and approve it next.', 'success');
      await fetchServers();
    } catch (err) {
      console.error(err);
      toast(err instanceof Error ? err.message : 'Connector registration failed.', 'error');
    } finally {
      setAdding(false);
    }
  };

  const act = async (server: MCPServer, action: 'approve' | 'revoke' | 'start' | 'stop' | 'restart' | 'delete') => {
    setBusyId(server.server_id);
    try {
      if (action === 'approve') await mcp.approveConsent(server.server_id, server.command_fingerprint, approvedScopes);
      if (action === 'revoke') await mcp.revokeConsent(server.server_id);
      if (action === 'start') await mcp.startServer(server.server_id);
      if (action === 'stop') await mcp.stopServer(server.server_id);
      if (action === 'restart') await mcp.restartServer(server.server_id);
      if (action === 'delete') await mcp.deleteServer(server.server_id);
      toast(`Connector ${action} completed.`, 'success');
      setReviewServer(null);
      await fetchServers();
    } catch (err) {
      console.error(err);
      toast(err instanceof Error ? err.message : `Connector ${action} failed.`, 'error');
    } finally {
      setBusyId('');
    }
  };

  const activeCount = useMemo(() => servers.filter((server) => server.status === 'active').length, [servers]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 text-sm">
            <Link href="/admin/mcp" className="text-muted-foreground hover:text-primary">MCP</Link>
            <span className="text-muted-foreground">/</span><span className="font-semibold">Connectors</span>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">Managed MCP connectors</h1>
          <p className="text-muted-foreground">Register an exact local program, review its access, then approve and start it.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => void fetchServers()}><RefreshCw className="mr-2 h-4 w-4" />Refresh</Button>
          <Button onClick={() => setAddOpen(true)}><Plus className="mr-2 h-4 w-4" />Register connector</Button>
        </div>
      </div>

      <Card className="border-amber-500/30 bg-amber-500/5">
        <CardContent className="p-4 text-sm">
          External connectors are disabled until you approve the exact command and scopes. Network-capable connectors are blocked, and Windows file-isolation qualification remains a release gate.
        </CardContent>
      </Card>
      {error && <div className="rounded-md border border-red-200 bg-red-50 p-4 text-red-700" role="alert">{error}</div>}

      <div className="grid gap-4 sm:grid-cols-3">
        <Card><CardContent className="p-4"><div className="text-sm text-muted-foreground">Registered</div><div className="text-2xl font-bold">{servers.length}</div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="text-sm text-muted-foreground">Running</div><div className="text-2xl font-bold">{activeCount}</div></CardContent></Card>
        <Card><CardContent className="p-4"><div className="text-sm text-muted-foreground">Transport</div><div className="text-2xl font-bold">Local stdio</div></CardContent></Card>
      </div>

      {loading ? <Card><CardContent className="p-8 text-center text-muted-foreground">Loading connectors…</CardContent></Card> : servers.length === 0 ? (
        <Card><CardContent className="p-8 text-center text-muted-foreground">No external connectors are registered.</CardContent></Card>
      ) : (
        <div className="grid gap-4 xl:grid-cols-2">
          {servers.map((server) => (
            <Card key={server.server_id}>
              <CardHeader className="pb-3"><CardTitle className="flex items-center justify-between gap-3 text-lg"><span className="flex min-w-0 items-center gap-2"><Box className="h-4 w-4 shrink-0 text-blue-500" /><span className="truncate">{server.name}</span></span><Badge variant={server.status === 'active' ? 'default' : 'outline'}>{server.status}</Badge></CardTitle></CardHeader>
              <CardContent className="space-y-4 text-sm">
                <div className="grid grid-cols-2 gap-3">
                  <div><div className="text-muted-foreground">Consent</div><div className="font-medium capitalize">{server.consent_state}</div></div>
                  <div><div className="text-muted-foreground">Health</div><div className="font-medium capitalize">{qualificationLabel(server.health_status)}</div></div>
                </div>
                <div><div className="text-muted-foreground">Exact command</div><code className="mt-1 block break-all rounded bg-muted p-2 text-xs">{commandPreview(server)}</code></div>
                <div><div className="text-muted-foreground">Approved folder</div><code className="break-all text-xs">{server.config.file_roots.join(', ')}</code></div>
                <div><div className="text-muted-foreground">Containment</div><div className="text-xs capitalize">{qualificationLabel(server.containment_status)}</div></div>
                {server.last_error_message && <div className="rounded border border-red-500/20 bg-red-500/5 p-2 text-red-700">{server.last_error_message}</div>}
                <div className="flex flex-wrap gap-2">
                  {server.consent_state !== 'approved' && <Button size="sm" onClick={() => { setApprovedScopes(server.requested_scopes); setReviewServer(server); }}><ShieldCheck className="mr-2 h-4 w-4" />Review and approve</Button>}
                  {server.consent_state === 'approved' && server.status !== 'active' && <Button size="sm" onClick={() => void act(server, 'start')} disabled={busyId === server.server_id}><Play className="mr-2 h-4 w-4" />Start</Button>}
                  {server.status === 'active' && <Button size="sm" variant="outline" onClick={() => void act(server, 'stop')} disabled={busyId === server.server_id}><Pause className="mr-2 h-4 w-4" />Stop</Button>}
                  {server.status === 'active' && <Button size="sm" variant="outline" onClick={() => void act(server, 'restart')} disabled={busyId === server.server_id}><RotateCw className="mr-2 h-4 w-4" />Restart</Button>}
                  {server.consent_state === 'approved' && <Button size="sm" variant="outline" onClick={() => void act(server, 'revoke')} disabled={busyId === server.server_id}><ShieldOff className="mr-2 h-4 w-4" />Revoke</Button>}
                  <Button size="sm" variant="ghost" className="text-red-600" onClick={() => { if (confirm(`Delete ${server.name}?`)) void act(server, 'delete'); }} disabled={busyId === server.server_id}><Trash2 className="mr-2 h-4 w-4" />Delete</Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={addOpen} onOpenChange={setAddOpen}>
        <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
          <DialogHeader><DialogTitle>Register a local connector</DialogTitle><DialogDescription>Registration validates and stores the definition. It does not run the program.</DialogDescription></DialogHeader>
          <div className="grid gap-4 py-2 sm:grid-cols-2">
            <div className="space-y-2"><Label htmlFor="mcp-name">Name</Label><Input id="mcp-name" value={name} onChange={(event) => setName(event.target.value)} placeholder="documents" /></div>
            <div className="space-y-2"><Label htmlFor="mcp-version">Version</Label><Input id="mcp-version" value={version} onChange={(event) => setVersion(event.target.value)} /></div>
            <div className="space-y-2 sm:col-span-2"><Label htmlFor="mcp-description">Description</Label><Input id="mcp-description" value={description} onChange={(event) => setDescription(event.target.value)} /></div>
            <div className="space-y-2 sm:col-span-2"><Label htmlFor="mcp-command">Absolute executable path</Label><Input id="mcp-command" value={command} onChange={(event) => setCommand(event.target.value)} placeholder="C:\\Program Files\\Connector\\connector.exe" /></div>
            <div className="space-y-2 sm:col-span-2"><Label htmlFor="mcp-args">Arguments, one per line</Label><textarea id="mcp-args" className="min-h-20 w-full rounded-md border bg-background px-3 py-2 text-sm" value={argsText} onChange={(event) => setArgsText(event.target.value)} /></div>
            <div className="space-y-2"><Label htmlFor="mcp-cwd">Working folder</Label><Input id="mcp-cwd" value={cwd} onChange={(event) => setCwd(event.target.value)} /></div>
            <div className="space-y-2"><Label htmlFor="mcp-root">Approved file root</Label><Input id="mcp-root" value={fileRoot} onChange={(event) => setFileRoot(event.target.value)} /></div>
            <label className="flex items-center gap-2 text-sm sm:col-span-2"><input type="checkbox" checked={allowWrite} onChange={(event) => setAllowWrite(event.target.checked)} />Request write access in addition to read access</label>
            <div className="space-y-2 sm:col-span-2"><div className="font-medium">Optional protected credential</div><p className="text-xs text-muted-foreground">The secret is encrypted with Windows DPAPI and is never returned to this screen.</p></div>
            <div className="space-y-2"><Label htmlFor="mcp-env">Environment variable</Label><Input id="mcp-env" value={credentialEnv} onChange={(event) => setCredentialEnv(event.target.value)} placeholder="SERVICE_API_KEY" /></div>
            <div className="space-y-2"><Label htmlFor="mcp-ref">Reference name</Label><Input id="mcp-ref" value={credentialRef} onChange={(event) => setCredentialRef(event.target.value)} placeholder="service-key" /></div>
            <div className="space-y-2 sm:col-span-2"><Label htmlFor="mcp-secret">Secret value</Label><Input id="mcp-secret" type="password" value={credentialValue} onChange={(event) => setCredentialValue(event.target.value)} autoComplete="new-password" /></div>
          </div>
          <DialogFooter><Button variant="outline" onClick={() => setAddOpen(false)} disabled={adding}>Cancel</Button><Button onClick={() => void handleAddServer()} disabled={adding}>{adding && <RefreshCw className="mr-2 h-4 w-4 animate-spin" />}Validate and register</Button></DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={Boolean(reviewServer)} onOpenChange={(open) => { if (!open) setReviewServer(null); }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader><DialogTitle>Review exact connector authority</DialogTitle><DialogDescription>Approval applies only to this command fingerprint and the scopes selected below.</DialogDescription></DialogHeader>
          {reviewServer && <div className="space-y-4 text-sm">
            <div><div className="text-muted-foreground">Exact command</div><code className="mt-1 block break-all rounded bg-muted p-3">{commandPreview(reviewServer)}</code></div>
            <div><div className="text-muted-foreground">Fingerprint</div><code className="break-all text-xs">{reviewServer.command_fingerprint}</code></div>
            <div className="space-y-2"><div className="font-medium">Requested access</div>{reviewServer.requested_scopes.map((scope) => <label key={scope} className="flex items-center gap-2"><input type="checkbox" checked={approvedScopes.includes(scope)} onChange={(event) => setApprovedScopes((current) => event.target.checked ? [...new Set([...current, scope])] : current.filter((value) => value !== scope))} />{scope}</label>)}</div>
            <div className="rounded border border-amber-500/30 bg-amber-500/5 p-3">Connector results are treated as untrusted data. Network destinations are not permitted.</div>
          </div>}
          <DialogFooter><Button variant="outline" onClick={() => setReviewServer(null)}>Cancel</Button>{reviewServer && <Button onClick={() => void act(reviewServer, 'approve')} disabled={!approvedScopes.length || busyId === reviewServer.server_id}><ShieldCheck className="mr-2 h-4 w-4" />Approve exact command</Button>}</DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

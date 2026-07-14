'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Database, Server, HardDrive, Network, Zap, 
  CheckCircle, XCircle, RefreshCw, Play, Square,
  Laptop, Settings2, AlertCircle, Archive
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { request } from '@/lib/api';
import { useToast } from '@/components/ui/use-toast';

interface ServiceStatus {
  healthy: boolean;
  url?: string;
  is_cloud: boolean;
  provider?: string;
  endpoint?: string;
  state?: string;
  safe_reason?: string | null;
  version?: string;
  expected_version?: string;
  expected_identity?: string;
  observed_identity?: string;
}

interface StorageHealth {
  mode: string;
  services: {
    postgres: ServiceStatus;
    redis: ServiceStatus;
    neo4j: ServiceStatus;
    vector: ServiceStatus;
    object: ServiceStatus;
  };
}

interface AutoStartResponse {
  enabled?: boolean;
  message?: string;
}

interface LifecycleResponse {
  success?: boolean;
  message?: string;
}

interface DesktopStorageMetrics {
  generated_at: string;
  runtime_root: string;
  sqlite: Record<string, unknown>;
  neo4j: Record<string, unknown>;
  chroma: Record<string, unknown>;
  object_store: Record<string, unknown>;
  structured_memory: Record<string, unknown>;
  total_local_bytes: number;
}

interface DesktopBackupResult {
  artifact_path: string;
  size_bytes: number;
  manifest: Record<string, unknown>;
}

const SERVICE_ICONS: Record<string, React.ElementType> = {
  postgres: Database,
  redis: Zap,
  neo4j: Network,
  vector: HardDrive,
  object: Server,
};

const SERVICE_LABELS: Record<string, string> = {
  postgres: 'PostgreSQL',
  redis: 'Redis',
  neo4j: 'Neo4j',
  vector: 'Vector DB',
  object: 'Object Storage',
};

function formatErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }
  return String(error);
}

function formatBytes(value: unknown): string {
  const bytes = typeof value === 'number' ? value : 0;
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

function isStorageHealth(value: unknown): value is StorageHealth {
  if (!value || typeof value !== 'object') return false;
  const candidate = value as Partial<StorageHealth>;
  if (!candidate.services || typeof candidate.services !== 'object') return false;
  const requiredKeys: Array<keyof StorageHealth['services']> = ['postgres', 'redis', 'neo4j', 'vector', 'object'];
  return requiredKeys.every((key) => Boolean(candidate.services && key in candidate.services));
}

export function DatabaseSettings() {
  const { toast } = useToast();
  const [health, setHealth] = useState<StorageHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [lifecycleAction, setLifecycleAction] = useState<'start' | 'stop' | null>(null);
  const [mode, setMode] = useState('internal');
  const [autoStartEnabled, setAutoStartEnabled] = useState(false);
  const [savingAutoStart, setSavingAutoStart] = useState(false);
  const [activeTab, setActiveTab] = useState('status');
  const [desktopMetrics, setDesktopMetrics] = useState<DesktopStorageMetrics | null>(null);
  const [backupRunning, setBackupRunning] = useState(false);
  const [backupOperationId, setBackupOperationId] = useState<string | null>(null);
  const [backupRecoverySecret, setBackupRecoverySecret] = useState('');
  const [backupRecoveryConfirmation, setBackupRecoveryConfirmation] = useState('');
  const [lastBackup, setLastBackup] = useState<DesktopBackupResult | null>(null);
  const fetchHealth = useCallback(async () => {
    try {
      const [healthData, autoStartData, metricsData] = await Promise.all([
        request<StorageHealth>('/storage/health'),
        request<AutoStartResponse>('/storage/databases/autostart').catch(() => null),
        window.electronAPI?.getDesktopStorageMetrics
          ? window.electronAPI.getDesktopStorageMetrics().catch(() => null)
          : request<DesktopStorageMetrics>('/storage/desktop-metrics').catch(() => null),
      ]);

      if (isStorageHealth(healthData)) {
        setHealth(healthData);
        setMode(healthData.mode || 'internal');
      } else {
        setHealth(null);
        toast('Storage health response format was invalid.', 'warning');
      }

      if (autoStartData && typeof autoStartData.enabled === 'boolean') {
        setAutoStartEnabled(autoStartData.enabled);
      }
      setDesktopMetrics(metricsData);
    } catch (error) {
      console.error('Failed to fetch storage health:', error);
      toast(`Failed to fetch storage health: ${formatErrorMessage(error)}`, 'error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [toast]);

  useEffect(() => {
    let cancelled = false;
    async function init() {
      await fetchHealth();
      if (cancelled) return;
    }
    void init();
    return () => { cancelled = true; };
  }, [fetchHealth]);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchHealth();
  };

  const handleTestConnection = async (service: string) => {
    setTesting(service);
    try {
      await request(`/storage/health/${service}`);
      await fetchHealth();
      toast(`${SERVICE_LABELS[service] || service} health check complete.`, 'success', 2000);
    } catch (error) {
      console.error(`Failed to test ${service}:`, error);
      toast(`Failed to test ${SERVICE_LABELS[service] || service}: ${formatErrorMessage(error)}`, 'error');
    } finally {
      setTesting(null);
    }
  };

  const handleStartDatabases = async () => {
    if (lifecycleAction) return;
    setLifecycleAction('start');
    try {
      const result = await request<LifecycleResponse>('/storage/databases/start', { method: 'POST' });
      toast(result.message || 'Database startup initiated.', 'success');
      setTimeout(fetchHealth, 1200);
    } catch (error) {
      console.error('Failed to start databases:', error);
      toast(`Failed to start databases: ${formatErrorMessage(error)}`, 'error');
    } finally {
      setLifecycleAction(null);
    }
  };

  const handleStopDatabases = async () => {
    if (lifecycleAction) return;
    setLifecycleAction('stop');
    try {
      const result = await request<LifecycleResponse>('/storage/databases/stop', { method: 'POST' });
      toast(result.message || 'Database shutdown initiated.', 'success');
      setTimeout(fetchHealth, 1000);
    } catch (error) {
      console.error('Failed to stop databases:', error);
      toast(`Failed to stop databases: ${formatErrorMessage(error)}`, 'error');
    } finally {
      setLifecycleAction(null);
    }
  };

  const handleAutoStartChange = async (enabled: boolean) => {
    const previous = autoStartEnabled;
    setAutoStartEnabled(enabled);
    setSavingAutoStart(true);
    try {
      const result = await request<AutoStartResponse>('/storage/databases/autostart', {
        method: 'POST',
        body: JSON.stringify({ enabled }),
      });
      if (typeof result.enabled === 'boolean') {
        setAutoStartEnabled(result.enabled);
      }
      toast(result.message || 'Auto-start preference saved.', 'success', 2000);
    } catch (error) {
      setAutoStartEnabled(previous);
      toast(`Failed to save auto-start preference: ${formatErrorMessage(error)}`, 'error');
    } finally {
      setSavingAutoStart(false);
    }
  };

  const handleBackup = async () => {
    if (backupRecoverySecret.length < 12) {
      toast('Use a recovery passphrase with at least 12 characters.', 'error');
      return;
    }
    if (backupRecoverySecret !== backupRecoveryConfirmation) {
      toast('Recovery passphrases do not match.', 'error');
      return;
    }
    setBackupRunning(true);
    try {
      let target_capability: string | undefined;
      if (window.electronAPI?.chooseBackupFolder) {
        const selected = await window.electronAPI.chooseBackupFolder();
        if (!selected) {
          setBackupRunning(false);
          return;
        }
        target_capability = selected.token;
      }

      if (!window.electronAPI?.runDatabaseBackup) {
        throw new Error('Database backup is available only in the desktop application.');
      }
      const operation_id = crypto.randomUUID();
      setBackupOperationId(operation_id);
      const result = await window.electronAPI.runDatabaseBackup({
        target_capability,
        operation_id,
        recovery_secret: backupRecoverySecret,
      });
      setLastBackup(result);
      setBackupRecoverySecret('');
      setBackupRecoveryConfirmation('');
      toast('Database backup completed.', 'success', 3000);
      void fetchHealth();
    } catch (error) {
      toast(`Backup failed: ${formatErrorMessage(error)}`, 'error');
    } finally {
      setBackupOperationId(null);
      setBackupRunning(false);
    }
  };

  const cancelBackup = async () => {
    if (!backupOperationId || !window.electronAPI?.cancelDesktopOperation) return;
    const result = await window.electronAPI.cancelDesktopOperation(backupOperationId);
    if (result.cancelled) {
      toast('Backup cancellation requested.', 'success', 3000);
    }
  };

  const renderServiceCard = (serviceKey: string, status: ServiceStatus) => {
    const Icon = SERVICE_ICONS[serviceKey] || Database;
    const label = SERVICE_LABELS[serviceKey] || serviceKey;
    
    return (
      <Card key={serviceKey} className="relative overflow-hidden">
        <div className={`absolute top-0 left-0 w-1 h-full ${status.healthy ? 'bg-green-500' : 'bg-red-500'}`} />
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Icon className="h-5 w-5 text-muted-foreground" />
              <CardTitle className="text-base">{label}</CardTitle>
            </div>
            <Badge variant={status.healthy ? 'default' : 'destructive'}>
              {status.healthy ? (
                <><CheckCircle className="h-3 w-3 mr-1" /> Online</>
              ) : (
                <><XCircle className="h-3 w-3 mr-1" /> Offline</>
              )}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2 text-muted-foreground">
              <><Laptop className="h-4 w-4" /> App-owned internal service</>
            </div>
            {status.url && (
              <p className="text-xs text-muted-foreground truncate" title={status.url}>
                {status.url}
              </p>
            )}
            {status.provider && (
              <p className="text-xs text-muted-foreground">
                Provider: {status.provider}
              </p>
            )}
            {status.version && (
              <p className="text-xs text-muted-foreground">Version: {status.version}</p>
            )}
            {status.safe_reason && (
              <p className="text-xs text-red-600 dark:text-red-400">
                Reason: {status.safe_reason}
              </p>
            )}
            <Button 
              size="sm" 
              variant="outline" 
              className="w-full mt-2"
              onClick={() => handleTestConnection(serviceKey)}
              disabled={testing === serviceKey}
            >
              {testing === serviceKey ? (
                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Settings2 className="h-4 w-4 mr-2" />
              )}
              Test Connection
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8" role="status" aria-live="polite">
        <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" aria-hidden="true" />
        <span className="sr-only">Loading database status…</span>
      </div>
    );
  }

  const healthyCount = health ? Object.values(health.services).filter(s => s.healthy).length : 0;
  const totalCount = health ? Object.keys(health.services).length : 5;

  return (
    <div className="space-y-6" aria-busy={refreshing || lifecycleAction !== null || backupRunning}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Internal Data Plane</h2>
          <p className="text-muted-foreground">
            Operate the app-owned internal data plane
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Status Overview */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="flex items-center gap-4">
              <div className={`p-3 rounded-full ${healthyCount === totalCount ? 'bg-green-100 dark:bg-green-900' : 'bg-yellow-100 dark:bg-yellow-900'}`}>
                {healthyCount === totalCount ? (
                  <CheckCircle className="h-6 w-6 text-green-600 dark:text-green-400" />
                ) : (
                  <AlertCircle className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
                )}
              </div>
              <div>
                <p className="font-medium">
                  {healthyCount}/{totalCount} Services Online
                </p>
                <div className="text-sm text-muted-foreground">
                  Mode: <Badge variant="secondary">{mode.toUpperCase()}</Badge>
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleStartDatabases} disabled={lifecycleAction !== null}>
                {lifecycleAction === 'start' ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                {lifecycleAction === 'start' ? 'Starting...' : 'Start All'}
              </Button>
              <Button variant="outline" onClick={handleStopDatabases} disabled={lifecycleAction !== null}>
                {lifecycleAction === 'stop' ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Square className="h-4 w-4 mr-2" />
                )}
                {lifecycleAction === 'stop' ? 'Stopping...' : 'Stop All'}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Service Cards */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList>
          <TabsTrigger value="status">Status</TabsTrigger>
          <TabsTrigger value="metrics">Metrics & Backup</TabsTrigger>
          <TabsTrigger value="local">Runtime Policy</TabsTrigger>
        </TabsList>

        <TabsContent value="status" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {health && Object.entries(health.services).map(([key, status]) => 
              renderServiceCard(key, status)
            )}
          </div>
        </TabsContent>

        <TabsContent value="metrics" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HardDrive className="h-5 w-5" />
                Local Storage Metrics
              </CardTitle>
              <CardDescription>
                Runtime storage footprint and local database inventory
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {desktopMetrics ? (
                <>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                    {[
                      ['SQLite', desktopMetrics.sqlite],
                      ['Neo4j', desktopMetrics.neo4j],
                      ['Chroma', desktopMetrics.chroma],
                      ['Objects', desktopMetrics.object_store],
                    ].map(([label, metric]) => {
                      const data = (metric ?? {}) as Record<string, unknown>;
                      return (
                        <div key={label as string} className="rounded-md border p-3">
                          <div className="text-xs text-muted-foreground uppercase">{label as string}</div>
                          <div className="text-lg font-semibold">{formatBytes(data?.size_bytes)}</div>
                          {'tables' in data && (
                            <div className="text-xs text-muted-foreground">
                              {String(data.tables)} tables, {String(data.rows)} rows
                            </div>
                          )}
                          {'exists' in data && (
                            <div className="text-xs text-muted-foreground">
                              {data.exists ? 'Present' : 'Not created'}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                  <div className="rounded-md border p-3 text-sm">
                    <div className="font-medium">Runtime root</div>
                    <div className="text-xs text-muted-foreground break-all">{desktopMetrics.runtime_root}</div>
                    <div className="mt-2 text-xs text-muted-foreground">
                      Total local data: {formatBytes(desktopMetrics.total_local_bytes)}
                    </div>
                  </div>
                </>
              ) : (
                <div className="rounded-md border p-3 text-sm text-muted-foreground">
                  Desktop metrics are not available yet.
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Archive className="h-5 w-5" />
                Backup
              </CardTitle>
              <CardDescription>
                Create a portable archive of local desktop storage
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <Label htmlFor="backup-recovery-secret">Recovery passphrase</Label>
                <Input
                  id="backup-recovery-secret"
                  type="password"
                  autoComplete="new-password"
                  value={backupRecoverySecret}
                  onChange={(event) => setBackupRecoverySecret(event.target.value)}
                  disabled={backupRunning}
                />
                <Label htmlFor="backup-recovery-confirmation">Confirm recovery passphrase</Label>
                <Input
                  id="backup-recovery-confirmation"
                  type="password"
                  autoComplete="new-password"
                  value={backupRecoveryConfirmation}
                  onChange={(event) => setBackupRecoveryConfirmation(event.target.value)}
                  disabled={backupRunning}
                />
                <p className="text-xs text-muted-foreground">
                  This passphrase is not stored. You will need it to restore the encrypted backup.
                </p>
              </div>
              <Button onClick={handleBackup} disabled={backupRunning}>
                {backupRunning ? (
                  <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Archive className="h-4 w-4 mr-2" />
                )}
                {backupRunning ? 'Backing Up...' : 'Run Backup'}
              </Button>
              {backupOperationId && (
                <Button variant="outline" onClick={() => void cancelBackup()} aria-label="Cancel database backup">
                  Cancel backup
                </Button>
              )}
              {lastBackup && (
                <div className="rounded-md border p-3 text-sm">
                  <div className="font-medium">Last backup</div>
                  <div className="text-xs text-muted-foreground break-all">{lastBackup.artifact_path}</div>
                  <div className="text-xs text-muted-foreground">{formatBytes(lastBackup?.size_bytes)}</div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="local" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Laptop className="h-5 w-5" />
                Internal Data-Plane Policy
              </CardTitle>
              <CardDescription>
                Ports, paths, credentials, and immutable versions are installation-owned and read-only.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {health && Object.entries(health.services).map(([key, status]) => (
                  <div key={key} className="rounded-md border p-3 text-sm">
                    <div className="font-medium">{SERVICE_LABELS[key] || key}</div>
                    <div className="text-xs text-muted-foreground break-all">
                      {status.endpoint || status.url || 'Endpoint unavailable'}
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {status.expected_version
                        ? `Locked version ${status.expected_version}`
                        : 'Version pending'}
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex items-center space-x-2 pt-4">
                <Switch
                  id="auto-start"
                  checked={autoStartEnabled}
                  onCheckedChange={handleAutoStartChange}
                  disabled={savingAutoStart}
                />
                <Label htmlFor="auto-start">
                  {savingAutoStart
                    ? 'Saving auto-start preference...'
                    : 'Auto-start databases on application launch'}
                </Label>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

      </Tabs>
    </div>
  );
}

export default DatabaseSettings;

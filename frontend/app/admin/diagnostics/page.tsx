'use client';

import { useState } from 'react';
import useSWR from 'swr';
import {
  Activity,
  FileSearch,
  HardDrive,
  PackageCheck,
  RefreshCw,
  ShieldCheck,
} from 'lucide-react';

import { ConfirmationDialog } from '@/components/ConfirmationDialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';
import { api } from '@/lib/api';
import type { SupportBundleArtifact, SupportBundlePreview } from '@/lib/api/diagnostics';

function formatBytes(value: number): string {
  if (!Number.isFinite(value) || value < 0) return 'Not measured';
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DiagnosticsPage() {
  const { toast } = useToast();
  const { data, error, isLoading, mutate } = useSWR(
    'system.diagnostics.summary',
    () => api.diagnostics.summary(),
  );
  const [preview, setPreview] = useState<SupportBundlePreview | null>(null);
  const [artifact, setArtifact] = useState<SupportBundleArtifact | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const handlePreview = async () => {
    setPreviewing(true);
    setArtifact(null);
    try {
      const nextPreview = await api.diagnostics.previewSupportBundle();
      setPreview(nextPreview);
      toast('Redacted support bundle preview is ready.', 'success');
    } catch {
      setPreview(null);
      toast('Support bundle preview could not be created.', 'error');
    } finally {
      setPreviewing(false);
    }
  };

  const handleExport = async () => {
    if (!preview) return;
    setExporting(true);
    try {
      const nextArtifact = await api.diagnostics.exportSupportBundle(
        preview.preview_fingerprint,
      );
      setArtifact(nextArtifact);
      toast('Redacted support bundle generated locally.', 'success');
    } catch {
      setPreview(null);
      toast('The preview changed or the bundle could not be generated. Preview it again.', 'error');
    } finally {
      setExporting(false);
    }
  };

  const services = data?.runtime?.services ? Object.entries(data.runtime.services) : [];

  return (
    <div className="container mx-auto p-8 space-y-8">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Diagnostics</h1>
          <p className="text-muted-foreground">
            Review local capability state and create redacted support evidence.
          </p>
        </div>
        <Button variant="outline" onClick={() => void mutate()} disabled={isLoading}>
          <RefreshCw className="mr-2 h-4 w-4" aria-hidden="true" />
          Refresh diagnostics
        </Button>
      </header>

      {error ? (
        <div role="alert" className="rounded-md border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
          Diagnostics are unavailable. No healthy state is being assumed.
        </div>
      ) : isLoading || !data ? (
        <p className="text-sm text-muted-foreground" role="status">Loading diagnostic state...</p>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" aria-hidden="true" /> Runtime
              </CardTitle>
              <CardDescription>Current backend lifecycle and request state.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between gap-4"><span>Phase</span><Badge variant="outline">{data.runtime.phase}</Badge></div>
              <div className="flex justify-between gap-4"><span>Ready</span><span>{data.runtime.ready ? 'Yes' : 'No'}</span></div>
              <div className="flex justify-between gap-4"><span>Requests</span><span>{data.requests.total}</span></div>
              <div className="flex justify-between gap-4"><span>In progress</span><span>{data.requests.inflight}</span></div>
              <div className="flex justify-between gap-4"><span>Correlation ID</span><code className="break-all text-xs">{data.correlation_id}</code></div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HardDrive className="h-5 w-5" aria-hidden="true" /> Local services
              </CardTitle>
              <CardDescription>Supervisor-reported state; an open port alone is not health.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              {services.length === 0 ? (
                <p className="text-muted-foreground">No managed service state was returned.</p>
              ) : services.map(([name, service]) => (
                <div key={name} className="flex items-center justify-between gap-4 rounded-md border p-2">
                  <span className="font-medium capitalize">{name}</span>
                  <Badge variant="outline">{service.state || 'unknown'}</Badge>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ShieldCheck className="h-5 w-5" aria-hidden="true" /> Privacy boundary
              </CardTitle>
              <CardDescription>Diagnostic collection and external telemetry truth.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div className="flex justify-between gap-4"><span>External telemetry</span><span>{data.external_telemetry.enabled ? 'Enabled by opt-in' : 'Disabled'}</span></div>
              <div className="flex justify-between gap-4"><span>Log schema</span><code>{data.logging.schema_version}</code></div>
              <div className="flex justify-between gap-4"><span>User content in bundle</span><span>{data.support_bundle.user_content_included ? 'Included' : 'Excluded'}</span></div>
              <div className="flex justify-between gap-4"><span>Generic reports</span><span>{data.support_bundle.generic_reports_included ? 'Included' : 'Excluded'}</span></div>
              <p className="text-xs text-muted-foreground">
                Redaction is deterministic and tested, but preview the file inventory before sharing any artifact.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileSearch className="h-5 w-5" aria-hidden="true" /> Support bundle
              </CardTitle>
              <CardDescription>Preview first; generation writes one hashed archive to the application support folder.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                <Button variant="outline" onClick={() => void handlePreview()} disabled={previewing || exporting}>
                  <FileSearch className="mr-2 h-4 w-4" aria-hidden="true" />
                  {previewing ? 'Building preview...' : 'Preview bundle'}
                </Button>
                <Button onClick={() => setConfirmOpen(true)} disabled={!preview || exporting}>
                  <PackageCheck className="mr-2 h-4 w-4" aria-hidden="true" />
                  {exporting ? 'Generating...' : 'Generate local bundle'}
                </Button>
              </div>

              {preview && (
                <div className="space-y-2 rounded-md border p-3 text-sm">
                  <p className="font-medium">Previewed files ({preview.files.length})</p>
                  <ul className="max-h-44 space-y-1 overflow-auto" aria-label="Support bundle file preview">
                    {preview.files.map((file) => (
                      <li key={file.path} className="flex justify-between gap-3 text-xs">
                        <code className="break-all">{file.path}</code>
                        <span className="shrink-0 text-muted-foreground">{formatBytes(file.size_bytes)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {artifact && (
                <div role="status" className="space-y-1 rounded-md border border-green-600/40 bg-green-600/10 p-3 text-sm">
                  <p className="font-medium">Bundle generated locally</p>
                  <p className="break-all">{artifact.artifact_name} ({formatBytes(artifact.size_bytes)})</p>
                  <p className="break-all text-xs">SHA-256: {artifact.sha256}</p>
                  <p className="text-xs text-muted-foreground">Location: application support-bundles folder</p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      <ConfirmationDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        onConfirm={() => void handleExport()}
        title="Generate redacted support bundle?"
        description="This writes the previewed diagnostic file classes to the local application support-bundles folder and creates a SHA-256 sidecar. It does not upload anything."
        riskTier="write"
        confirmLabel="Generate bundle"
      />
    </div>
  );
}

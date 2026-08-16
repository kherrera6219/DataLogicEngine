'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Select, SelectItem } from '@/components/ui/select';
import { Database, Download, ShieldCheck, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { request } from '@/lib/api';

interface ExporterStats {
  status: string;
  total_trace_runs: number;
  release_candidate_runs: number;
  supported_types: string[];
  supported_formats: string[];
  pyarrow_available: boolean;
  redaction_enforced: boolean;
}

type ExportType = 'sft' | 'prm';
type FormatType = 'parquet' | 'jsonl';

export default function DatasetExporterSettings() {
  const [enabled, setEnabled] = useState(false);
  const [exportType, setExportType] = useState<ExportType>('sft');
  const [formatType, setFormatType] = useState<FormatType>('parquet');
  const [minConfidence, setMinConfidence] = useState('0.98');

  const [stats, setStats] = useState<ExporterStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const data = await request<ExporterStats>('/dataset/stats');
      setStats(data);
    } catch {
      setStats(null);
      setMessage({ type: 'error', text: 'Dataset statistics are unavailable.' });
    } finally {
      setLoading(false);
    }
  };

  const handleEnabledChange = (value: boolean) => {
    setEnabled(value);
    if (value) void fetchStats();
  };

  const handleRunExport = async () => {
    if (!enabled) return;
    setExporting(true);
    setMessage(null);

    try {
      const result = await request<{ status: string; exported_rows: number; artifact_name: string }>('/dataset/export', {
        method: 'POST',
        body: JSON.stringify({
          export_type: exportType,
          format_type: formatType,
          min_confidence: parseFloat(minConfidence),
        }),
      });

      setMessage({
        type: 'success',
        text: `Export complete. Created ${result.artifact_name} with ${result.exported_rows} rows.`,
      });
      void fetchStats();
    } catch (err) {
      setMessage({
        type: 'error',
        text: err instanceof Error ? err.message : 'Dataset export failed.',
      });
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="h-5 w-5 text-primary" />
            Dataset preparation & export (no in-app trainer)
          </CardTitle>
          <CardDescription>
            Manually create candidate SFT or status-labelled PRM records from explicitly released traces.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Master Enable Toggle */}
          <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
            <div className="space-y-0.5">
              <Label className="text-base font-medium">Enable manual export controls</Label>
              <p className="text-sm text-muted-foreground">
                This does not start a background job. Each export requires an explicit owner action.
              </p>
            </div>
            <Switch
              checked={enabled}
              onCheckedChange={handleEnabledChange}
              aria-label="Toggle dataset exporter"
            />
          </div>

          {enabled && (
            <>
              {/* Configuration Controls */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="export-type-select">Default Dataset Format</Label>
                  <Select
                    id="export-type-select"
                    value={exportType}
                    onChange={(event) => setExportType(event.target.value as ExportType)}
                  >
                    <SelectItem value="sft">SFT (Supervised Fine-Tuning)</SelectItem>
                    <SelectItem value="prm">PRM candidate (status-derived labels)</SelectItem>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="format-type-select">Output File Serialization</Label>
                  <Select
                    id="format-type-select"
                    value={formatType}
                    onChange={(event) => setFormatType(event.target.value as FormatType)}
                  >
                    <SelectItem value="parquet">Apache Parquet (.parquet)</SelectItem>
                    <SelectItem value="jsonl">Line-Delimited JSON (.jsonl)</SelectItem>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="min-confidence-select">Minimum Confidence Threshold</Label>
                  <Select
                    id="min-confidence-select"
                    value={minConfidence}
                    onChange={(event) => setMinConfidence(event.target.value)}
                  >
                    <SelectItem value="0.95">0.95 (lower threshold)</SelectItem>
                    <SelectItem value="0.98">0.98 (default threshold)</SelectItem>
                    <SelectItem value="0.995">0.995 (strict threshold)</SelectItem>
                  </Select>
                </div>

                <div className="space-y-2 flex items-center justify-between p-3 border rounded-lg">
                  <div className="space-y-0.5">
                    <Label className="text-sm font-medium flex items-center gap-1.5">
                      <ShieldCheck className="h-4 w-4 text-emerald-500" />
                      Privacy & Secret Redaction
                    </Label>
                    <p className="text-xs text-muted-foreground">Always enforced; it cannot be disabled.</p>
                  </div>
                  <span className="text-xs font-semibold text-emerald-600">Enforced</span>
                </div>
              </div>

              {/* Status Summary Card */}
              <div className="p-4 rounded-lg border bg-muted/40 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">System Status</span>
                  <Button variant="ghost" size="sm" onClick={fetchStats} disabled={loading}>
                    <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                  </Button>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-sm">
                  <div>
                    <span className="text-muted-foreground block text-xs">Total Traces</span>
                    <span className="font-semibold">{loading ? '…' : (stats?.total_trace_runs ?? 'Unavailable')}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-xs">Release candidates (&ge;0.98)</span>
                    <span className="font-semibold text-emerald-600">{loading ? '…' : (stats?.release_candidate_runs ?? 'Unavailable')}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block text-xs">PyArrow Status</span>
                    <span className="font-semibold">{stats?.pyarrow_available ? 'Available' : 'JSONL Fallback'}</span>
                  </div>
                </div>
              </div>

              {/* Action Banner Message */}
              {message && (
                <div
                  className={`p-3 rounded-lg border flex items-center gap-2 text-sm ${
                    message.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'
                  }`}
                >
                  {message.type === 'success' ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  ) : (
                    <AlertCircle className="h-4 w-4 text-red-600 shrink-0" />
                  )}
                  <span>{message.text}</span>
                </div>
              )}

              {/* Run Export Trigger Button */}
              <div className="flex justify-end pt-2">
                <Button onClick={handleRunExport} disabled={exporting}>
                  <Download className="h-4 w-4 mr-2" />
                  {exporting ? 'Exporting Dataset...' : 'Trigger Dataset Export Batch'}
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

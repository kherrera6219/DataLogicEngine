import { request } from './client';

export interface DiagnosticsSummary {
  schema_version: 'dle.diagnostics.v1';
  status: string;
  runtime: {
    phase: string;
    ready: boolean;
    services: Record<string, { state?: string; safe_reason?: string | null }>;
  };
  requests: {
    total: number;
    inflight: number;
    uptime_seconds: number;
  };
  logging: {
    schema_version: string;
    format: string;
    redaction: string;
  };
  external_telemetry: {
    opted_in: boolean;
    enabled: boolean;
    provider: string;
    state_code: string | null;
  };
  support_bundle: {
    schema_version: string;
    content_policy: string;
    user_content_included: boolean;
    generic_reports_included: boolean;
    preview_required: boolean;
    encryption_available_via_cli: boolean;
  };
  correlation_id: string;
  timestamp: string;
}

export interface SupportBundlePreviewFile {
  path: string;
  size_bytes: number;
  sha256: string;
  classification: string;
}

export interface SupportBundlePreview {
  schema_version: string;
  archive_created: false;
  content_policy: string;
  user_content_included: false;
  preview_fingerprint: string;
  files: SupportBundlePreviewFile[];
}

export interface SupportBundleArtifact {
  success: true;
  artifact_name: string;
  sidecar_name: string;
  sha256: string;
  size_bytes: number;
  encrypted: boolean;
  location: 'application_support_bundles_directory';
  timestamp: string;
}

export const diagnostics = {
  summary: () => request<DiagnosticsSummary>('/system/diagnostics/summary'),
  previewSupportBundle: () =>
    request<SupportBundlePreview>('/system/diagnostics/support/preview', { method: 'POST' }),
  exportSupportBundle: (previewFingerprint: string) =>
    request<SupportBundleArtifact>('/system/diagnostics/support/export', {
      method: 'POST',
      body: JSON.stringify({
        confirm: true,
        preview_fingerprint: previewFingerprint,
      }),
    }),
};

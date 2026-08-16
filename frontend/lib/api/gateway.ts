import { request } from './client';

export const GATEWAY_SCOPES = [
  'chat',
  'stream',
  'run:create',
  'run:read',
  'run:cancel',
  'trace:read',
  'evidence:read',
  'models:read',
  'routing:override',
] as const;

export type GatewayScope = typeof GATEWAY_SCOPES[number];

export interface ClientKeyMetadata {
  id: string;
  name: string;
  key_prefix: string;
  is_active: boolean;
  scopes: GatewayScope[];
  total_requests: number;
  last_used_at: string | null;
  created_at: string;
  expires_at: string | null;
  revoked_at: string | null;
  revoked_reason: string | null;
  allowed_providers: string[];
  allowed_models: string[];
  rate_limit_rpm: number;
  rate_limit_daily: number | null;
  max_tokens_per_request: number | null;
  max_concurrent_requests: number;
}

export interface ClientKeyCreate extends Record<string, unknown> {
  name: string;
  scopes: GatewayScope[];
  expires_in_days?: number;
  rate_limit_rpm: number;
  rate_limit_daily?: number;
  max_tokens_per_request?: number;
  max_concurrent_requests: number;
}

export interface CopyOnceClientKey extends ClientKeyMetadata {
  api_key: string;
  warning: string;
}

export interface GatewayCapabilities {
  contract_version: string;
  profile: 'desktop_loopback' | 'same_host_gateway';
  virtual_models: Record<string, {
    mode?: string;
    max_provider_calls?: number;
    description?: string;
  }>;
  scopes: string[];
  provider_credentials_exposed: false;
  /** G-GEN=B0: generative answers use cloud BYOK; data plane stays local. */
  generative_locality?: 'cloud_byok' | 'local' | 'hybrid';
  local_model_acceleration?: boolean;
}

export interface GatewayControlPlaneStatus {
  gateway_contract_version: string;
  profile: string;
  bind_addresses: string[];
  private_gateway_enabled: boolean;
  private_gateway_qualified: boolean;
  tls: { state: string; certificate: string | null };
  mtls: { state: string };
  firewall: { state: string };
  cors: { state: string };
  dependencies: Record<string, { state: string; required: boolean }>;
}

export interface GatewayAuditEvent {
  id: number;
  timestamp: string | null;
  action: string;
  details: Record<string, unknown>;
}

export const gateway = {
  capabilities: () => request<GatewayCapabilities>('/gateway/capabilities'),
  controlPlaneStatus: () => request<GatewayControlPlaneStatus>('/admin/gateway/status'),
  health: () => request<Record<string, unknown>>('/gateway/health'),
  usage: () => request<Record<string, unknown>>('/gateway/usage-ledger?days=30'),
  jobs: () => request<{ jobs: Array<Record<string, unknown>> }>('/gateway/runs?limit=25'),
  // P2-02: gateway admin is under /admin/gateway/* (ops admin remains /admin/health, etc.)
  clientKeys: () => request<{ api_keys: ClientKeyMetadata[] }>('/admin/gateway/api-keys'),
  clientKeyAudit: () => request<{ events: GatewayAuditEvent[] }>('/admin/gateway/api-keys/audit?limit=100'),
  createClientKey: (payload: ClientKeyCreate) => request<CopyOnceClientKey>('/admin/gateway/api-keys', {
    method: 'POST',
    body: JSON.stringify(payload),
  }),
  rotateClientKey: (id: string, overlapSeconds = 300) => request<CopyOnceClientKey>(
    `/admin/gateway/api-keys/${id}/rotate`,
    { method: 'POST', body: JSON.stringify({ overlap_seconds: overlapSeconds }) },
  ),
  revokeClientKey: (id: string, reason: string) => request<{ message: string }>(
    `/admin/gateway/api-keys/${id}/revoke`,
    { method: 'POST', body: JSON.stringify({ reason }) },
  ),
  expireClientKey: (id: string, reason: string) => request<{ message: string }>(
    `/admin/gateway/api-keys/${id}/expire`,
    { method: 'POST', body: JSON.stringify({ reason }) },
  ),
  deleteClientKey: (id: string) => request<{ message: string }>(`/admin/gateway/api-keys/${id}`, {
    method: 'DELETE',
  }),
};

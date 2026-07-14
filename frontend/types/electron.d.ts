import type { IngestionResult, KAExecutionFeed } from '../lib/api/types';

export interface DesktopUpdateState {
  enabled: boolean;
  status:
    | 'disabled'
    | 'idle'
    | 'checking'
    | 'available'
    | 'not_available'
    | 'downloaded'
    | 'error';
  lastCheckAt: string | null;
  currentVersion: string;
  availableVersion: string | null;
  message: string;
}

export interface DesktopDatabaseStatus {
  status: string;
  phase: string;
  services: Record<string, { state?: string; safe_reason?: string | null }>;
  chroma_collections: Record<string, number>;
  redis_ping_ms: number | null;
  object_store_buckets: Record<string, { object_count: number; total_bytes: number }>;
  memory_vertices: number;
  memory_edges: number;
  last_recall_timestamp: string | null;
}

export interface QuadAnalysisStatus {
  pod_count: number;
  collective_confidence: number;
  mode: string;
}

export interface DMRFStatus {
  status: string;
  tier?: string | null;
  frost_depth?: number | null;
  run_id?: string | null;
  tier_counts?: Record<string, number>;
}

export interface DSQPPersonaProfile {
  axis: number;
  persona_type: string;
  name: string;
  coverage_score: number;
  job_role: string;
  skills: string[];
  chain_steps: number;
}

export interface DSQPPersonaProfilesStatus {
  success: boolean;
  profiles: DSQPPersonaProfile[];
  partial: boolean;
  failures: Record<string, string>;
}

export interface DesktopNetworkStatus {
  state: 'ONLINE' | 'DEGRADED' | 'OFFLINE' | string;
  last_checked: string;
  active_provider: string | null;
  details?: Record<string, unknown>;
}

export interface LocalModelStatus {
  ollama_available: boolean;
  models_installed: string[];
  active_model: string | null;
}

export interface ReasoningLayerProgress {
  active_run_id: string | null;
  status: string;
  current_layer: number | null;
  layer_name: string | null;
  kas_running: Array<{
    ka_id: string;
    ka_name?: string | null;
    status?: string;
    confidence?: number | null;
    duration_ms?: number | null;
  }>;
  confidence_so_far: number | null;
  persona_confidences: Array<{
    persona: string;
    persona_type?: string;
    confidence: number;
    status?: string;
  }>;
  frost_snapshot_count: number;
  updated_at: string;
}

export interface DesktopStorageMetrics {
  generated_at: string;
  runtime_root: string;
  sqlite: Record<string, unknown>;
  neo4j: Record<string, unknown>;
  chroma: Record<string, unknown>;
  object_store: Record<string, unknown>;
  structured_memory: Record<string, unknown>;
  total_local_bytes: number;
}

export interface DesktopBackupResult {
  artifact_path: string;
  size_bytes: number;
  manifest: Record<string, unknown>;
}

export interface DesktopPathCapability {
  token: string;
  display_name: string;
  expires_at: string;
}

export interface DesktopIngestionRequest {
  source_capability: string;
  recursive: boolean;
  chunk_size: number;
  max_file_bytes: number;
  max_total_bytes: number;
  max_files: number;
  max_pages: number;
  max_archive_entries: number;
  max_decompressed_bytes: number;
  max_archive_depth: number;
  parser_timeout_seconds: number;
  source_label?: string;
  async_mode: boolean;
  sync_neo4j: boolean;
  operation_id: string;
}

export type DesktopIngestionResult =
  | IngestionResult
  | { ingestion_id: string; status: string };

export interface ElectronAPI {
  ping: () => Promise<string>;
  getBackendStatus: () => Promise<string>;
  getDbStatus: () => Promise<DesktopDatabaseStatus>;
  quadAnalysisStatus: () => Promise<QuadAnalysisStatus>;
  dmrfStatus: () => Promise<DMRFStatus>;
  dsqpPersonaProfiles: () => Promise<DSQPPersonaProfilesStatus>;
  getNetworkStatus: () => Promise<DesktopNetworkStatus>;
  getLocalModelStatus: () => Promise<LocalModelStatus>;
  getReasoningLayerProgress: () => Promise<ReasoningLayerProgress>;
  getKAExecutionFeed: () => Promise<KAExecutionFeed>;
  getDesktopStorageMetrics: () => Promise<DesktopStorageMetrics | null>;
  chooseBackupFolder: () => Promise<DesktopPathCapability | null>;
  runDatabaseBackup: (payload: { target_capability?: string; operation_id: string; recovery_secret: string }) => Promise<DesktopBackupResult>;
  chooseIngestionSource: () => Promise<DesktopPathCapability | null>;
  runLocalIngestion: (payload: DesktopIngestionRequest) => Promise<DesktopIngestionResult>;
  cancelDesktopOperation: (operationId: string) => Promise<{ cancelled: boolean }>;
  getUpdateState: () => Promise<DesktopUpdateState>;
  checkForUpdates: () => Promise<DesktopUpdateState>;
  downloadUpdate: () => Promise<DesktopUpdateState>;
  onBackendLog: (callback: (log: string) => void) => () => void;
  onBackendError: (callback: (error: string) => void) => () => void;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}

export interface ReleaseTrustPolicy {
  schema_version?: string;
  signing?: {
    production_authorized?: boolean;
    expected_publisher_subjects?: unknown[];
  };
  updates?: {
    production_qualified?: boolean;
    signed_metadata_qualified?: boolean;
    publisher_verification_qualified?: boolean;
    downgrade_prevention_qualified?: boolean;
    replay_prevention_qualified?: boolean;
    interrupted_update_rollback_qualified?: boolean;
    staged_rollout_qualified?: boolean;
    offline_signed_update_qualified?: boolean;
  };
}

export interface UpdateTrustDecision {
  allowed: boolean;
  reason: string;
}

const REQUIRED_UPDATE_GATES: Array<keyof NonNullable<ReleaseTrustPolicy['updates']>> = [
  'production_qualified',
  'signed_metadata_qualified',
  'publisher_verification_qualified',
  'downgrade_prevention_qualified',
  'replay_prevention_qualified',
  'interrupted_update_rollback_qualified',
  'staged_rollout_qualified',
  'offline_signed_update_qualified',
];

export function evaluateUpdateTrustPolicy(policy: ReleaseTrustPolicy | null): UpdateTrustDecision {
  if (!policy || policy.schema_version !== 'dle.release-trust-policy.v1') {
    return { allowed: false, reason: 'release trust policy is missing or invalid' };
  }
  if (policy.signing?.production_authorized !== true) {
    return { allowed: false, reason: 'production publisher signing is not authorized' };
  }
  if (!Array.isArray(policy.signing.expected_publisher_subjects)
      || policy.signing.expected_publisher_subjects.length === 0) {
    return { allowed: false, reason: 'approved publisher identity is not configured' };
  }
  const missingGate = REQUIRED_UPDATE_GATES.find((gate) => policy.updates?.[gate] !== true);
  if (missingGate) {
    return { allowed: false, reason: `update qualification gate is open: ${missingGate}` };
  }
  return { allowed: true, reason: 'signed update trust policy is qualified' };
}

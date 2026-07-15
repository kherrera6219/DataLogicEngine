import { describe, expect, it } from 'vitest';

import { evaluateUpdateTrustPolicy, type ReleaseTrustPolicy } from './update-trust';


function qualifiedPolicy(): ReleaseTrustPolicy {
  return {
    schema_version: 'dle.release-trust-policy.v1',
    signing: {
      production_authorized: true,
      expected_publisher_subjects: ['CN=Approved Publisher'],
    },
    updates: {
      production_qualified: true,
      signed_metadata_qualified: true,
      publisher_verification_qualified: true,
      downgrade_prevention_qualified: true,
      replay_prevention_qualified: true,
      interrupted_update_rollback_qualified: true,
      staged_rollout_qualified: true,
      offline_signed_update_qualified: true,
    },
  };
}

describe('evaluateUpdateTrustPolicy', () => {
  it('rejects the checked-in pre-production policy state', () => {
    const policy = qualifiedPolicy();
    policy.updates!.downgrade_prevention_qualified = false;

    expect(evaluateUpdateTrustPolicy(policy)).toEqual({
      allowed: false,
      reason: 'update qualification gate is open: downgrade_prevention_qualified',
    });
  });

  it('rejects a policy without an approved publisher', () => {
    const policy = qualifiedPolicy();
    policy.signing!.expected_publisher_subjects = [];

    expect(evaluateUpdateTrustPolicy(policy).allowed).toBe(false);
  });

  it('allows updates only after every trust gate passes', () => {
    expect(evaluateUpdateTrustPolicy(qualifiedPolicy())).toEqual({
      allowed: true,
      reason: 'signed update trust policy is qualified',
    });
  });
});

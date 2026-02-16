export type FeatureFlagKey =
  | 'cloudDisclosureBanner'
  | 'strictInputSanitization'
  | 'storyA11yChecks'
  | 'visualRegressionGate'
  | 'enterpriseThemeOverrides';

export type FeatureFlagSource = 'default' | 'cloud' | 'enterprise' | 'local';

export interface FeatureFlagDefinition {
  key: FeatureFlagKey;
  description: string;
  defaultValue: boolean;
  localOverrideAllowed: boolean;
}

export type FeatureFlagState = Record<FeatureFlagKey, boolean>;
export type FeatureFlagSources = Record<FeatureFlagKey, FeatureFlagSource>;

export const FEATURE_FLAG_DEFINITIONS: Record<FeatureFlagKey, FeatureFlagDefinition> = {
  cloudDisclosureBanner: {
    key: 'cloudDisclosureBanner',
    description: 'Controls the cloud disclosure banner rendered in the primary shell.',
    defaultValue: true,
    localOverrideAllowed: true,
  },
  strictInputSanitization: {
    key: 'strictInputSanitization',
    description: 'Applies client-side payload sanitization before API requests.',
    defaultValue: true,
    localOverrideAllowed: false,
  },
  storyA11yChecks: {
    key: 'storyA11yChecks',
    description: 'Enables Storybook accessibility checks for WCAG gates.',
    defaultValue: true,
    localOverrideAllowed: true,
  },
  visualRegressionGate: {
    key: 'visualRegressionGate',
    description: 'Enforces visual screenshot assertions in Playwright smoke checks.',
    defaultValue: true,
    localOverrideAllowed: true,
  },
  enterpriseThemeOverrides: {
    key: 'enterpriseThemeOverrides',
    description: 'Allows enterprise theme-token overrides to be applied at runtime.',
    defaultValue: true,
    localOverrideAllowed: true,
  },
};

export const FEATURE_FLAG_KEYS = Object.keys(FEATURE_FLAG_DEFINITIONS) as FeatureFlagKey[];

export function createDefaultFeatureFlagState(): FeatureFlagState {
  const state = {} as FeatureFlagState;
  for (const key of FEATURE_FLAG_KEYS) {
    state[key] = FEATURE_FLAG_DEFINITIONS[key].defaultValue;
  }
  return state;
}

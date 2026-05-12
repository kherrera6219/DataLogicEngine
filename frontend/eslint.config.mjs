// For more info, see https://github.com/storybookjs/eslint-plugin-storybook#configuration-flat-config-format
import storybook from "eslint-plugin-storybook";

import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "dist-electron/**",
    "dist/**",
    "dist-smoke/**",
    // Generated artifacts and debug outputs
    "storybook-static/**",
    "test-results/**",
    "playwright-report/**",
    "*.log",
    "*.txt",
    "lint-results.json",
  ]),
  ...storybook.configs["flat/recommended"],
  {
    rules: {
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": "warn",
      // Project uses @storybook/react with Next.js — suppress advisory rule
      "storybook/no-renderer-packages": "off",
    },
  },
  {
    files: ["lib/**/*.ts", "lib/**/*.tsx"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: [
            "@/app/*",
            "@/components/*",
            "@/contexts/*",
            "../app/*",
            "../components/*",
            "../contexts/*",
            "../../app/*",
            "../../components/*",
            "../../contexts/*",
          ],
        },
      ],
    },
  },
  {
    files: ["contexts/**/*.ts", "contexts/**/*.tsx"],
    rules: {
      "no-restricted-imports": [
        "error",
        {
          patterns: ["@/app/*", "../app/*", "../../app/*"],
        },
      ],
    },
  },
  {
    files: ["**/*.ts", "**/*.tsx"],
    ignores: [
      "lib/state/storage.ts",
      "**/*.test.ts",
      "**/*.test.tsx",
      "tests/**",
      "**/*.stories.tsx",
    ],
    rules: {
      "no-restricted-globals": [
        "error",
        {
          name: "localStorage",
          message: "Use frontend/lib/state/storage.ts helpers for persistent client state.",
        },
        {
          name: "sessionStorage",
          message: "Use frontend/lib/state/storage.ts helpers for persistent client state.",
        },
      ],
      "no-restricted-properties": [
        "error",
        {
          object: "window",
          property: "localStorage",
          message: "Use frontend/lib/state/storage.ts helpers for persistent client state.",
        },
        {
          object: "window",
          property: "sessionStorage",
          message: "Use frontend/lib/state/storage.ts helpers for persistent client state.",
        },
      ],
    },
  },
  {
    files: ["**/*.test.ts", "**/*.test.tsx"],
    rules: {
      "@typescript-eslint/no-explicit-any": "off",
    },
  },
]);

export default eslintConfig;

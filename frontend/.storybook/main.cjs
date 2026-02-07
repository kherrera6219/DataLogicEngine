/* eslint-disable @typescript-eslint/no-require-imports */
/** @type { import('@storybook/react-vite').StorybookConfig } */
const config = {
  stories: [
    "../stories/**/*.mdx",
    "../stories/**/*.stories.@(js|jsx|mjs|ts|tsx)"
  ],
  addons: [
    "@chromatic-com/storybook",
    "@storybook/addon-essentials",
    "@storybook/addon-interactions",
    "@storybook/addon-links",
    "@storybook/addon-onboarding"
  ],
  framework: {
    name: "@storybook/react-vite",
    options: {}
  },
  staticDirs: [
    "../public"
  ],
  docs: {
    autodocs: "tag"
  },
  viteFinal: async (config) => {
    config.resolve = config.resolve || {};
    config.resolve.alias = config.resolve.alias || {};
    config.resolve.alias['next/config'] = require.resolve('./next-config-mock.js');
    return config;
  }
};
module.exports = config;

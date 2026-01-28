const path = require('path');

/** @type { import('@storybook/nextjs').StorybookConfig } */
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
    name: "@storybook/nextjs",
    options: {}
  },
  staticDirs: [
    "../public"
  ],
  docs: {
    autodocs: "tag"
  }
};
module.exports = config;

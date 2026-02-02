import type { Meta, StoryObj } from '@storybook/react';
import { ApiOverlayConfig } from '@/components/settings/ApiOverlayConfig';

const meta: Meta<typeof ApiOverlayConfig> = {
  title: 'Settings/ApiOverlayConfig',
  component: ApiOverlayConfig,
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof ApiOverlayConfig>;

export const Default: Story = {};

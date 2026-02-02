import type { Meta, StoryObj } from '@storybook/react';
import DatabaseSettings from '@/components/settings/DatabaseSettings';

const meta: Meta<typeof DatabaseSettings> = {
  title: 'Settings/DatabaseSettings',
  component: DatabaseSettings,
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof DatabaseSettings>;

export const Default: Story = {};

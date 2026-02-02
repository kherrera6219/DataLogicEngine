import type { Meta, StoryObj } from '@storybook/react';
import { CommandBar } from '@/components/Dashboard/CommandBar';

const meta: Meta<typeof CommandBar> = {
  title: 'Dashboard/CommandBar',
  component: CommandBar,
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof CommandBar>;

export const Default: Story = {};

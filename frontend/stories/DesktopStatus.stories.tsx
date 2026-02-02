import type { Meta, StoryObj } from '@storybook/react';
import { DesktopStatus } from '@/components/DesktopStatus';

const meta: Meta<typeof DesktopStatus> = {
  title: 'Layout/DesktopStatus',
  component: DesktopStatus,
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof DesktopStatus>;

export const Default: Story = {};

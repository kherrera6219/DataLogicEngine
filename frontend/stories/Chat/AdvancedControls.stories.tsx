import type { Meta, StoryObj } from '@storybook/react';
import { AdvancedControls } from '@/components/Chat/AdvancedControls';

const meta: Meta<typeof AdvancedControls> = {
  title: 'Chat/AdvancedControls',
  component: AdvancedControls,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof AdvancedControls>;

export const Default: Story = {};

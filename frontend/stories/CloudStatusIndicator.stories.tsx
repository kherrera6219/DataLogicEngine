import type { Meta, StoryObj } from '@storybook/react';
import { CloudStatusIndicator } from '@/components/ui/cloud-status-indicator';

const meta = {
  title: 'Fluent UI/Components/CloudStatusIndicator',
  component: CloudStatusIndicator,
  tags: ['autodocs'],
} satisfies Meta<typeof CloudStatusIndicator>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => <CloudStatusIndicator />,
};

export const Processing: Story = {
  args: {
    isProcessing: true,
  },
};

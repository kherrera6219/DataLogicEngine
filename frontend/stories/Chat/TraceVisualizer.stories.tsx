import type { Meta, StoryObj } from '@storybook/react';
import { TraceVisualizer } from '@/components/Chat/TraceVisualizer';

const meta: Meta<typeof TraceVisualizer> = {
  title: 'Chat/TraceVisualizer',
  component: TraceVisualizer,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof TraceVisualizer>;

export const Default: Story = {};

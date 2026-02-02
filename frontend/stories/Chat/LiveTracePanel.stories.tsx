import type { Meta, StoryObj } from '@storybook/react';
import { LiveTracePanel } from '@/components/Chat/LiveTracePanel';

const meta: Meta<typeof LiveTracePanel> = {
  title: 'Chat/LiveTracePanel',
  component: LiveTracePanel,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof LiveTracePanel>;

export const Default: Story = {
    args: {
        isActive: true,
        currentStep: "Analyzing query constraints..."
    }
};

export const Idle: Story = {
    args: {
        isActive: false,
        currentStep: "Idle"
    }
};

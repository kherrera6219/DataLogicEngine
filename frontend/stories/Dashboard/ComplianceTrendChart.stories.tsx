import type { Meta, StoryObj } from '@storybook/react';
import { ComplianceTrendChart } from '@/components/Dashboard/ComplianceTrendChart';

const meta: Meta<typeof ComplianceTrendChart> = {
  title: 'Dashboard/ComplianceTrendChart',
  component: ComplianceTrendChart,
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof ComplianceTrendChart>;

export const Default: Story = {};

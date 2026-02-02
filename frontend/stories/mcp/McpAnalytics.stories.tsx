import type { Meta, StoryObj } from '@storybook/react';
import { McpAnalytics } from '@/components/mcp/McpAnalytics';

const meta: Meta<typeof McpAnalytics> = {
  title: 'MCP/McpAnalytics',
  component: McpAnalytics,
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof McpAnalytics>;

export const Default: Story = {};

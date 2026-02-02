import type { Meta, StoryObj } from '@storybook/react';
import { McpClientConfig } from '@/components/mcp/McpClientConfig';

const meta: Meta<typeof McpClientConfig> = {
  title: 'MCP/McpClientConfig',
  component: McpClientConfig,
  parameters: {
    layout: 'padded',
  },
};

export default meta;
type Story = StoryObj<typeof McpClientConfig>;

export const Default: Story = {};

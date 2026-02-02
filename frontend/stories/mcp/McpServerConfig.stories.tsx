import type { Meta, StoryObj } from '@storybook/react';
import { McpServerConfig } from '@/components/mcp/McpServerConfig';

const meta: Meta<typeof McpServerConfig> = {
  title: 'MCP/McpServerConfig',
  component: McpServerConfig,
  parameters: {
    layout: 'padded',
  },
};

export default meta;
type Story = StoryObj<typeof McpServerConfig>;

export const Default: Story = {};

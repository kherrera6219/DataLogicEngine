import type { Meta, StoryObj } from '@storybook/react';
import { McpHub } from '@/components/mcp/McpHub';

const meta: Meta<typeof McpHub> = {
  title: 'MCP/McpHub',
  component: McpHub,
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof McpHub>;

export const Default: Story = {};

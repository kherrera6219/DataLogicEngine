import type { Meta, StoryObj } from '@storybook/react';
import { McpIntegrationExamples } from '@/components/mcp/McpIntegrationExamples';

const meta: Meta<typeof McpIntegrationExamples> = {
  title: 'MCP/McpIntegrationExamples',
  component: McpIntegrationExamples,
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof McpIntegrationExamples>;

export const Default: Story = {};

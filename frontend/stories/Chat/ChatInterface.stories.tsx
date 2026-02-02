import type { Meta, StoryObj } from '@storybook/react';
import { ChatInterface } from '@/components/Chat/ChatInterface';

const meta: Meta<typeof ChatInterface> = {
  title: 'Chat/ChatInterface',
  component: ChatInterface,
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof ChatInterface>;

export const Default: Story = {};

import type { Meta, StoryObj } from '@storybook/react';
import MessageBubble from '@/components/Chat/MessageBubble';

const meta: Meta<typeof MessageBubble> = {
  title: 'Chat/MessageBubble',
  component: MessageBubble,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof MessageBubble>;

const userMessage = {
    id: "1",
    role: "user" as const,
    content: "Explain the compliance risks of using legacy databases.",
    timestamp: new Date().toISOString()
};

const aiMessage = {
    id: "2",
    role: "assistant" as const,
    content: "Legacy databases pose significant risks regarding data encryption at rest and audit trail integrity...",
    timestamp: new Date().toISOString(),
    personas: [
        { id: "1", name: "Security", role: "Audit", confidence: 0.99, contribution: "Risk Analysis", weight: 0.5 }
    ]
};

export const UserMessage: Story = {
    args: {
        message: userMessage,
        isLast: false
    }
};

export const AssistantMessage: Story = {
    args: {
        message: aiMessage,
        isLast: true
    }
};

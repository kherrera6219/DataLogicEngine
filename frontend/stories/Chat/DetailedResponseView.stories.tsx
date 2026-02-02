import type { Meta, StoryObj } from '@storybook/react';
import { DetailedResponseView } from '@/components/Chat/DetailedResponseView';

const meta: Meta<typeof DetailedResponseView> = {
  title: 'Chat/DetailedResponseView',
  component: DetailedResponseView,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
};

export default meta;
type Story = StoryObj<typeof DetailedResponseView>;

const sampleMessage = {
    id: "1",
    role: "assistant",
    content: "This is a detailed response analysis.",
    personas: [
        { id: "p1", name: "Technologist", role: "Analysis", confidence: 0.95, contribution: "Provided technical depth", weight: 0.4, avatar: "/avatars/tech.png", sources: [] },
        { id: "p2", name: "Strategist", role: "Planning", confidence: 0.88, contribution: "Aligned with goals", weight: 0.6, avatar: "/avatars/strat.png", sources: [] }
    ],
    metrics: {
        latency: 120,
        tokens: 450,
        cost: 0.004,
        tier: "High"
    },
    traceId: "trace-123"
};

export const Default: Story = {
    args: {
        message: sampleMessage
    }
};

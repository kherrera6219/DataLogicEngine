import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MessageBubble } from './MessageBubble';
import { Message } from '@/lib/api';

// Mock copy button since it might have browser deps
vi.mock('@/components/ui/copy-button', () => ({
  CopyButton: () => <button>Copy</button>
}));

describe('MessageBubble', () => {
  it('should render user message correctly', () => {
    const message = {
      id: '1',
      role: 'user' as const,
      content: 'Hello AI',
      timestamp: new Date().toISOString()
    };
    render(<MessageBubble message={message as Message} />);
    expect(screen.getByText('Hello AI')).toBeInTheDocument();
    // User avatar check (indirectly via class or icon existence, difficult to test exact icon without more mocks, but text content is sufficient for now)
  });

  it('should render assistant message correctly', () => {
    const message = {
      id: '2',
      role: 'assistant' as const,
      content: 'Hello Human',
      timestamp: new Date().toISOString()
    };
    render(<MessageBubble message={message as Message} />);
    expect(screen.getByText('Hello Human')).toBeInTheDocument();
  });

  it('should show thinking state', () => {
    const message = {
      id: '3',
      role: 'assistant' as const,
      content: 'Thinking...',
      timestamp: new Date().toISOString()
    };
    render(<MessageBubble message={message as Message} isThinking={true} />);
    expect(screen.getByText('Reasoning Logic active')).toBeInTheDocument();
  });
});

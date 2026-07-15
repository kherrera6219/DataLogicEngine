
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProjectDetail } from './ProjectDetail';
import { api } from '@/lib/api';

vi.mock('@/lib/api', () => ({
  api: {
    chat: {
      listSessions: vi.fn(),
      getSessionMessages: vi.fn(),
    },
  },
}));

describe('ProjectDetail', () => {
  const mockBack = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    Object.defineProperty(window, 'history', {
      value: { back: mockBack },
      writable: true,
    });

    (api.chat.listSessions as any).mockResolvedValue({
      sessions: [
        {
          id: 'PROJ-123',
          user_id: 1,
          title: 'HIPAA Compliance Audit',
          created_at: '2026-01-01T08:00:00Z',
          updated_at: '2026-01-01T10:01:00Z',
        },
      ],
    });

    (api.chat.getSessionMessages as any).mockResolvedValue({
      messages: [
        {
          id: 'msg-1',
          role: 'user',
          content: 'hipaa_compliance_v1.pdf uploaded',
          timestamp: '2026-01-01T10:00:00Z',
        },
        {
          id: 'msg-2',
          role: 'assistant',
          content: 'Compliance score looks stable at 84%',
          timestamp: '2026-01-01T10:01:00Z',
        },
      ],
    });
  });

  it('renders session header and details', async () => {
    render(<ProjectDetail id="PROJ-123" />);

    expect(await screen.findByText('HIPAA Compliance Audit')).toBeInTheDocument();
    expect(screen.getByText(/ID: PROJ-123/)).toBeInTheDocument();
  });

  it('navigates back when back button is clicked', async () => {
    render(<ProjectDetail id="PROJ-123" />);
    await screen.findByText('HIPAA Compliance Audit');

    const backButton = screen.getByRole('button', { name: 'Go back' });
    fireEvent.click(backButton);
    expect(mockBack).toHaveBeenCalled();
  });

  it('renders message list from API', async () => {
    render(<ProjectDetail id="PROJ-123" />);

    expect(await screen.findByText('hipaa_compliance_v1.pdf uploaded')).toBeInTheDocument();
    expect(screen.getByText('Compliance score looks stable at 84%')).toBeInTheDocument();
    expect(screen.getByText('user')).toBeInTheDocument();
    expect(screen.getByText('assistant')).toBeInTheDocument();
  });

  it('renders session stats', async () => {
    render(<ProjectDetail id="PROJ-123" />);

    expect(await screen.findByText('Session Stats')).toBeInTheDocument();
    expect(screen.getByText('Total Messages')).toBeInTheDocument();
    expect(screen.getByText('Created')).toBeInTheDocument();
    expect(screen.getByText('Last Updated')).toBeInTheDocument();
  });

  it('exposes accessible navigation and filtering controls', async () => {
    render(<ProjectDetail id="PROJ-123" />);

    expect(await screen.findByRole('main', { name: 'Chat session detail' })).toBeInTheDocument();
    expect(screen.getByRole('textbox', { name: 'Filter session messages' })).toBeInTheDocument();
    expect(screen.getByRole('table', { name: 'Session messages' })).toBeInTheDocument();
    expect(screen.getByLabelText('Session statistics')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /upload files/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /create new note/i })).not.toBeInTheDocument();
  });
});

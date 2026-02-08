import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { DetailedResponseView } from './DetailedResponseView';
import { ChatMessage } from './types';

describe('DetailedResponseView', () => {
  const mockMessage: ChatMessage = {
    id: '1',
    role: 'assistant',
    content: 'Test content',
    timestamp: '10:00 AM',
    metrics: [
      { name: 'FACTUAL_ACCURACY', score: 0.99, status: 'pass', details: 'Accurate' }
    ],
    personas: [
      { id: 'p1', name: 'Expert', role: 'Role', confidence: 95, contribution: 'Contrib', avatar: 'E', weight: 0.5, sources: [] }
    ]
  };

  it('should render metrics', () => {
    render(<DetailedResponseView message={mockMessage} />);
    expect(screen.getByText('Validation Metrics')).toBeInTheDocument();
    expect(screen.getByText('Factual Accuracy')).toBeInTheDocument();
    expect(screen.getByText('99.0%')).toBeInTheDocument();
  });

  it('should render personas', () => {
    render(<DetailedResponseView message={mockMessage} />);
    expect(screen.getByText('Persona Analysis')).toBeInTheDocument();
    expect(screen.getByText('Expert')).toBeInTheDocument();
    expect(screen.getByText('Contrib')).toBeInTheDocument();
  });

  it('should render empty telemetry state', () => {
    render(
      <DetailedResponseView
        message={{
          id: '2',
          role: 'assistant',
          content: 'No telemetry',
          timestamp: '10:01 AM',
        }}
      />
    );
    expect(screen.getByText('No validation telemetry is available for this response yet.')).toBeInTheDocument();
  });
});

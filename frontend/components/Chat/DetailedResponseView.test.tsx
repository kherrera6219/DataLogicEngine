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
    expect(screen.getByRole('region', { name: /validation metrics/i })).toBeInTheDocument();
    expect(screen.getByRole('meter', { name: 'Factual Accuracy' })).toHaveAttribute('aria-valuenow', '99');
  });

  it('should render personas', () => {
    render(<DetailedResponseView message={mockMessage} />);
    expect(screen.getByText('Persona Analysis')).toBeInTheDocument();
    expect(screen.getByText('Expert')).toBeInTheDocument();
    expect(screen.getByText('Contrib')).toBeInTheDocument();
    expect(screen.getByRole('region', { name: /persona analysis/i })).toBeInTheDocument();
    expect(screen.getByRole('listitem', { name: /expert, role, confidence 95.0 percent/i })).toBeInTheDocument();
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

  it('should expose report and share actions with accessible names', () => {
    render(<DetailedResponseView message={mockMessage} />);
    expect(screen.getByRole('button', { name: /download validation report/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /share validation details/i })).toBeInTheDocument();
  });

  it('should render persona icon branches for multiple persona types', () => {
    render(
      <DetailedResponseView
        message={{
          ...mockMessage,
          personas: [
            { id: 'p1', name: 'Health Specialist', role: 'Medical Reviewer', confidence: 0.9, contribution: 'Health', avatar: 'H', weight: 0.5, sources: [] },
            { id: 'p2', name: 'Legal Counsel', role: 'Regulatory Advisor', confidence: 0.8, contribution: 'Legal', avatar: 'L', weight: 0.5, sources: [] },
            { id: 'p3', name: 'Cloud Operator', role: 'Sector Operations', confidence: 0.7, contribution: 'Ops', avatar: 'O', weight: 0.5, sources: [] },
            { id: 'p4', name: 'Security Lead', role: 'Compliance Officer', confidence: 0.6, contribution: 'Security', avatar: 'S', weight: 0.5, sources: [] },
          ],
        }}
      />,
    );

    expect(screen.getByText('Health Specialist')).toBeInTheDocument();
    expect(screen.getByText('Legal Counsel')).toBeInTheDocument();
    expect(screen.getByText('Cloud Operator')).toBeInTheDocument();
    expect(screen.getByText('Security Lead')).toBeInTheDocument();
  });

  it('should normalize non-finite metrics and missing contributions safely', () => {
    render(
      <DetailedResponseView
        message={{
          ...mockMessage,
          metrics: [{ name: 'risk_score', score: Number.NaN, status: 'warn', details: 'Unknown' }],
          personas: [{ id: 'p9', name: 'Fallback Persona', role: 'Generalist', confidence: 0.5, contribution: '', avatar: 'F', weight: 0.5, sources: [] }],
        }}
      />,
    );

    expect(screen.getByRole('meter', { name: 'Risk Score' })).toHaveAttribute('aria-valuenow', '0');
    expect(screen.getByText('No contribution details were captured for this persona.')).toBeInTheDocument();
  });
});

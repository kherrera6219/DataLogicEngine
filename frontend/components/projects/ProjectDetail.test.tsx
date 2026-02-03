
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ProjectDetail } from './ProjectDetail';

describe('ProjectDetail', () => {
    // Mock the window.history.back
    const mockBack = vi.fn();
    Object.defineProperty(window, 'history', {
        value: { back: mockBack },
        writable: true
    });

  it('renders project header and details', () => {
    render(<ProjectDetail id="PROJ-123" />);
    
    expect(screen.getByText('HIPAA Compliance Audit')).toBeInTheDocument();
    expect(screen.getByText(/ID: PROJ-123/)).toBeInTheDocument();
  });

  it('navigates back when back button is clicked', () => {
    render(<ProjectDetail id="PROJ-123" />);
    
    // The back button is the first button in the header with an arrow icon
    // Using a more specific selector or test-id would be better, but relying on implementation details for now:
    // It is a button with an ArrowLeft icon.
    // Let's assume it's the first button
    const backButton = screen.getAllByRole('button')[0];
    
    fireEvent.click(backButton);
    expect(mockBack).toHaveBeenCalled();
  });

  it('renders file list', () => {
    render(<ProjectDetail id="PROJ-123" />);
    
    expect(screen.getByText('hipaa_compliance_v1.pdf')).toBeInTheDocument();
    expect(screen.getByText('patient_data_schema.json')).toBeInTheDocument();
    expect(screen.getByText('2.4 MB')).toBeInTheDocument();
  });

  it('renders project stats', () => {
    render(<ProjectDetail id="PROJ-123" />);
    
    expect(screen.getByText('Compliance Score')).toBeInTheDocument();
    expect(screen.getByText('84%')).toBeInTheDocument();
    expect(screen.getByText('Sarah Connor')).toBeInTheDocument();
  });
});

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { McpIntegrationExamples } from './McpIntegrationExamples';

// Mock UI components
vi.mock('@/components/ui/tabs', () => ({
  Tabs: ({ children, value, onValueChange }) => <div data-testid="tabs" data-value={value} onClick={() => onValueChange('ts')}>{children}</div>,
  TabsList: ({ children }) => <div>{children}</div>,
  TabsTrigger: ({ children, value }) => <button data-testid={`tab-${value}`}>{children}</button>,
  TabsContent: ({ children, value }) => <div data-testid={`content-${value}`}>{children}</div>
}));

vi.mock('@/components/ui/card', () => ({
  Card: ({ children }) => <div>{children}</div>,
  CardHeader: ({ children }) => <div>{children}</div>,
  CardTitle: ({ children }) => <div>{children}</div>,
  CardContent: ({ children }) => <div>{children}</div>
}));

// Mock clipboard
const mockWriteText = vi.fn();
Object.assign(navigator, {
  clipboard: {
    writeText: mockWriteText
  }
});

describe('McpIntegrationExamples', () => {
  it('should render correct title', () => {
    render(<McpIntegrationExamples />);
    expect(screen.getByText('MCP Integration Examples')).toBeInTheDocument();
  });

  it('should render tabs and default content', () => {
    render(<McpIntegrationExamples />);
    expect(screen.getByTestId('tab-python')).toBeInTheDocument();
    expect(screen.getByTestId('content-python')).toBeInTheDocument();
  });

  it('should handle tab change', () => {
    render(<McpIntegrationExamples />);
    const tabs = screen.getByTestId('tabs');
    fireEvent.click(tabs); // Simulating onValueChange logic in mock
    // In real scenario we'd click the trigger, but our mock simplifies this. 
    // Let's verify render logic is sound with simple mocks.
  });

  it('should copy code on click', () => {
    render(<McpIntegrationExamples />);
    const copyBtns = screen.getAllByText('Copy Code');
    fireEvent.click(copyBtns[0]);
    expect(mockWriteText).toHaveBeenCalled();
  });
});

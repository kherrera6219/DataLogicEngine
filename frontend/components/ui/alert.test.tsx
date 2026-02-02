import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Alert, AlertTitle, AlertDescription } from './alert';

describe('Alert', () => {
  it('should render correctly', () => {
    render(
      <Alert>
        <AlertTitle>Heads up!</AlertTitle>
        <AlertDescription>You can add components to your app using the cli.</AlertDescription>
      </Alert>
    );

    expect(screen.getByText('Heads up!')).toBeInTheDocument();
    expect(screen.getByText('You can add components to your app using the cli.')).toBeInTheDocument();
  });

  it('should apply variant classes', () => {
    render(<Alert variant="destructive" data-testid="alert">Error</Alert>);
    expect(screen.getByTestId('alert')).toHaveClass('border-destructive/50'); 
    // Usually standard shadcn/ui destructive alert has this class. 
    // If it fails I will check content.
  });
});

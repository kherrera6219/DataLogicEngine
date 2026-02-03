import { render, screen } from '@testing-library/react';
import { expect, test, describe } from 'vitest';
import { PageLayout } from './page-layout';
import React from 'react';

describe('PageLayout', () => {
  test('renders children correctly', () => {
    render(
      <PageLayout>
        <div data-testid="child">Test Child</div>
      </PageLayout>
    );
    expect(screen.getByTestId('child')).toBeDefined();
    expect(screen.getByText('Test Child')).toBeDefined();
  });

  test('renders title and description', () => {
    render(
      <PageLayout title="Test Title" description="Test Description">
        <div>Content</div>
      </PageLayout>
    );
    expect(screen.getByText('Test Title')).toBeDefined();
    expect(screen.getByText('Test Description')).toBeDefined();
  });

  test('renders breadcrumbs when provided', () => {
    const breadcrumbs = [
      { label: 'Home', href: '/' },
      { label: 'Sub', href: '/sub' }
    ];
    render(
      <PageLayout breadcrumbs={breadcrumbs}>
        <div>Content</div>
      </PageLayout>
    );
    // Breadcrumbs component should be rendered
    expect(screen.getByText('Home')).toBeDefined();
    expect(screen.getByText('Sub')).toBeDefined();
  });

  test('renders actions when provided', () => {
    render(
      <PageLayout actions={<button>Click Me</button>}>
        <div>Content</div>
      </PageLayout>
    );
    expect(screen.getByRole('button', { name: /click me/i })).toBeDefined();
  });

  test('applies custom class names', () => {
    const { container } = render(
      <PageLayout className="custom-class" containerClassName="container-class">
        <div>Content</div>
      </PageLayout>
    );
    expect(container.firstChild).toHaveClass('custom-class');
    const innerContainer = container.querySelector('.max-w-7xl');
    expect(innerContainer).toHaveClass('container-class');
  });
});

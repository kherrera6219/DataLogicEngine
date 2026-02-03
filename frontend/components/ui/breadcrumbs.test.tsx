import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { Breadcrumbs } from './breadcrumbs';

describe('Breadcrumbs', () => {
  const items = [
    { label: 'Projects', href: '/projects' },
    { label: 'Project Alpha' }
  ];

  it('should render home link', () => {
    render(<Breadcrumbs items={items} />);
    const homeLink = screen.getByRole('link', { name: /back to dashboard/i });
    expect(homeLink).toBeInTheDocument();
    expect(homeLink.getAttribute('href')).toBe('/dashboard');
  });

  it('should render breadcrumb items', () => {
    render(<Breadcrumbs items={items} />);
    expect(screen.getByText('Projects')).toBeInTheDocument();
    expect(screen.getByText('Project Alpha')).toBeInTheDocument();
  });

  it('should render links for items with href', () => {
    render(<Breadcrumbs items={items} />);
    const proyectosLink = screen.getByRole('link', { name: 'Projects' });
    expect(proyectosLink).toBeInTheDocument();
    expect(proyectosLink.getAttribute('href')).toBe('/projects');
  });

  it('should render span for items without href', () => {
    render(<Breadcrumbs items={items} />);
    const lastItem = screen.getByText('Project Alpha');
    expect(lastItem.tagName).toBe('SPAN');
    expect(lastItem).toHaveClass('text-blue-500');
  });

  it('should set aria-current="page" on the last item', () => {
    render(<Breadcrumbs items={items} />);
    const lastItem = screen.getByText('Project Alpha');
    expect(lastItem.getAttribute('aria-current')).toBe('page');
  });
});

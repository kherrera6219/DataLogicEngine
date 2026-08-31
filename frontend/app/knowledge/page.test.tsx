import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import KnowledgePage from './page';

vi.mock('@/components/settings/KnowledgeIngestionSettings', () => ({
  default: () => <div>Authoritative ingestion workspace</div>,
}));

describe('KnowledgePage', () => {
  it('uses the authoritative ingestion workspace and keeps graph browsing separate', () => {
    render(<KnowledgePage />);

    expect(screen.getByText('Authoritative ingestion workspace')).toBeInTheDocument();
    expect(screen.getByText(/source revisions, materialization, and retrieval status/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Browse relationships/i })).toHaveAttribute('href', '/graph');
  });
});

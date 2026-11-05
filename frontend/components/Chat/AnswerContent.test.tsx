import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { AnswerContent } from './AnswerContent';

describe('AnswerContent', () => {
  it('renders headings, emphasis, lists, and code without executing markup', () => {
    render(<AnswerContent text={'### Details\n\n**Gravity** is useful.\n\n- First\n- Second\n\n```\n<script>alert(1)</script>\n```'} />);
    expect(screen.getByRole('heading', { name: 'Details', level: 3 })).toBeInTheDocument();
    expect(screen.getByText('Gravity').tagName).toBe('STRONG');
    expect(screen.getAllByRole('listitem')).toHaveLength(2);
    expect(screen.getByText('<script>alert(1)</script>')).toBeInTheDocument();
    expect(document.querySelector('script')).toBeNull();
  });

  it('preserves a displayed equation as accessible LaTeX text', () => {
    render(<AnswerContent text={'$$\na = r\\omega^2\n$$'} />);
    expect(screen.getByLabelText('Equation in LaTeX')).toHaveTextContent('a = r\\omega^2');
  });
});

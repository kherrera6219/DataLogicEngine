
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ThemeToggle } from './ThemeToggle';
import { useTheme } from '@/contexts/ThemeContext';

// Mock ThemeContext
vi.mock('@/contexts/ThemeContext', () => ({
  useTheme: vi.fn(),
}));

describe('ThemeToggle', () => {
    const mockSetTheme = vi.fn();

    it('renders System icon when theme is system', () => {
        (useTheme as any).mockReturnValue({ theme: 'system', setTheme: mockSetTheme, resolvedTheme: 'dark' });
        const { container } = render(<ThemeToggle />);
        // Monitor icon usually has a rect, line, path
        expect(container.querySelector('svg')).toBeInTheDocument(); 
        expect(screen.getByTitle('Theme: system')).toBeInTheDocument();
    });

  it('renders Moon icon when resolved theme is dark', () => {
    (useTheme as any).mockReturnValue({ theme: 'dark', setTheme: mockSetTheme, resolvedTheme: 'dark' });
    render(<ThemeToggle />);
    expect(screen.getByTitle('Theme: dark')).toBeInTheDocument();
  });

  it('renders Sun icon when resolved theme is light', () => {
    (useTheme as any).mockReturnValue({ theme: 'light', setTheme: mockSetTheme, resolvedTheme: 'light' });
    render(<ThemeToggle />);
    expect(screen.getByTitle('Theme: light')).toBeInTheDocument();
  });

  it('cycles themes correctly', () => {
    (useTheme as any).mockReturnValue({ theme: 'light', setTheme: mockSetTheme });
    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    
    // light -> dark
    fireEvent.click(button);
    expect(mockSetTheme).toHaveBeenCalledWith('dark');

    // Reset mock for next step
    mockSetTheme.mockClear();
    (useTheme as any).mockReturnValue({ theme: 'dark', setTheme: mockSetTheme });
    render(<ThemeToggle />);
    fireEvent.click(screen.getAllByRole('button')[1]); // Re-render adds new button, select last one (or use explicit re-render)
    // Actually simplicity, re-mock and check logic
  });
  
    it('cycles light -> dark', () => {
        (useTheme as any).mockReturnValue({ theme: 'light', setTheme: mockSetTheme });
        render(<ThemeToggle />);
        fireEvent.click(screen.getByRole('button'));
        expect(mockSetTheme).toHaveBeenCalledWith('dark');
    });

    it('cycles dark -> system', () => {
        (useTheme as any).mockReturnValue({ theme: 'dark', setTheme: mockSetTheme });
        render(<ThemeToggle />);
        fireEvent.click(screen.getByRole('button'));
        expect(mockSetTheme).toHaveBeenCalledWith('system');
    });

    it('cycles system -> light', () => {
        (useTheme as any).mockReturnValue({ theme: 'system', setTheme: mockSetTheme });
        render(<ThemeToggle />);
        fireEvent.click(screen.getByRole('button'));
        expect(mockSetTheme).toHaveBeenCalledWith('light');
    });

});

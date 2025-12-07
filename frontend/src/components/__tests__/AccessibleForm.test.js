/**
 * Accessible Form Component Tests
 * Tests for WCAG 2.2 form accessibility compliance
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe } from 'jest-axe';
import {
  AccessibleFormField,
  AccessibleTextarea,
  AccessibleSelect,
  AccessibleCheckbox,
  FormErrorSummary
} from '../accessibility/AccessibleForm';
import { ChakraProvider } from '@chakra-ui/react';

// Wrapper for Chakra components
const ChakraWrapper = ({ children }) => (
  <ChakraProvider>{children}</ChakraProvider>
);

describe('AccessibleFormField', () => {
  test('renders with accessible label', () => {
    render(
      <ChakraWrapper>
        <AccessibleFormField
          label="Username"
          name="username"
          value=""
          onChange={() => {}}
        />
      </ChakraWrapper>
    );

    const input = screen.getByLabelText('Username');
    expect(input).toBeInTheDocument();
  });

  test('marks required fields with asterisk and aria-required', () => {
    render(
      <ChakraWrapper>
        <AccessibleFormField
          label="Email"
          name="email"
          value=""
          onChange={() => {}}
          required
        />
      </ChakraWrapper>
    );

    const input = screen.getByLabelText(/email/i);
    expect(input).toHaveAttribute('aria-required', 'true');
    expect(screen.getByText('*')).toBeInTheDocument();
  });

  test('displays error message with aria-invalid', () => {
    render(
      <ChakraWrapper>
        <AccessibleFormField
          label="Email"
          name="email"
          value=""
          onChange={() => {}}
          error="Email is required"
        />
      </ChakraWrapper>
    );

    const input = screen.getByLabelText('Email');
    expect(input).toHaveAttribute('aria-invalid', 'true');
    expect(screen.getByText('Email is required')).toBeInTheDocument();
  });

  test('associates error message with input via aria-describedby', () => {
    render(
      <ChakraWrapper>
        <AccessibleFormField
          label="Email"
          name="email"
          value=""
          onChange={() => {}}
          error="Email is required"
        />
      </ChakraWrapper>
    );

    const input = screen.getByLabelText('Email');
    const ariaDescribedBy = input.getAttribute('aria-describedby');
    expect(ariaDescribedBy).toBeTruthy();

    const errorMessage = document.getElementById(ariaDescribedBy.split(' ')[0]);
    expect(errorMessage).toHaveTextContent('Email is required');
  });

  test('displays helper text', () => {
    render(
      <ChakraWrapper>
        <AccessibleFormField
          label="Password"
          name="password"
          value=""
          onChange={() => {}}
          helperText="Must be at least 8 characters"
        />
      </ChakraWrapper>
    );

    expect(screen.getByText('Must be at least 8 characters')).toBeInTheDocument();
  });

  test('has no accessibility violations', async () => {
    const { container } = render(
      <ChakraWrapper>
        <AccessibleFormField
          label="Username"
          name="username"
          value=""
          onChange={() => {}}
          helperText="Enter your username"
        />
      </ChakraWrapper>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

describe('AccessibleTextarea', () => {
  test('renders with character count for maxLength', () => {
    render(
      <ChakraWrapper>
        <AccessibleTextarea
          label="Description"
          name="description"
          value="Hello"
          onChange={() => {}}
          maxLength={100}
        />
      </ChakraWrapper>
    );

    expect(screen.getByText('95 characters remaining')).toBeInTheDocument();
  });

  test('announces character count to screen readers', () => {
    render(
      <ChakraWrapper>
        <AccessibleTextarea
          label="Description"
          name="description"
          value="Hello"
          onChange={() => {}}
          maxLength={100}
        />
      </ChakraWrapper>
    );

    const charCount = screen.getByText('95 characters remaining');
    expect(charCount.parentElement).toHaveAttribute('aria-live', 'polite');
  });

  test('has no accessibility violations', async () => {
    const { container } = render(
      <ChakraWrapper>
        <AccessibleTextarea
          label="Comments"
          name="comments"
          value=""
          onChange={() => {}}
          maxLength={200}
        />
      </ChakraWrapper>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

describe('AccessibleSelect', () => {
  const options = [
    { value: 'us', label: 'United States' },
    { value: 'uk', label: 'United Kingdom' },
    { value: 'ca', label: 'Canada' }
  ];

  test('renders with options', () => {
    render(
      <ChakraWrapper>
        <AccessibleSelect
          label="Country"
          name="country"
          value=""
          onChange={() => {}}
          options={options}
        />
      </ChakraWrapper>
    );

    const select = screen.getByLabelText('Country');
    expect(select).toBeInTheDocument();
    expect(screen.getByText('United States')).toBeInTheDocument();
  });

  test('has no accessibility violations', async () => {
    const { container } = render(
      <ChakraWrapper>
        <AccessibleSelect
          label="Country"
          name="country"
          value=""
          onChange={() => {}}
          options={options}
        />
      </ChakraWrapper>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

describe('AccessibleCheckbox', () => {
  test('renders with label', () => {
    render(
      <ChakraWrapper>
        <AccessibleCheckbox
          label="I agree to terms"
          name="terms"
          checked={false}
          onChange={() => {}}
        />
      </ChakraWrapper>
    );

    const checkbox = screen.getByRole('checkbox', { name: /i agree to terms/i });
    expect(checkbox).toBeInTheDocument();
  });

  test('has no accessibility violations', async () => {
    const { container } = render(
      <ChakraWrapper>
        <AccessibleCheckbox
          label="Subscribe to newsletter"
          name="newsletter"
          checked={false}
          onChange={() => {}}
        />
      </ChakraWrapper>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });
});

describe('FormErrorSummary', () => {
  const errors = [
    { fieldId: 'email', label: 'Email', message: 'Email is required' },
    { fieldId: 'password', label: 'Password', message: 'Password must be at least 8 characters' }
  ];

  test('renders error summary with correct count', () => {
    render(
      <ChakraWrapper>
        <FormErrorSummary errors={errors} />
      </ChakraWrapper>
    );

    expect(screen.getByText(/there are 2 errors in this form/i)).toBeInTheDocument();
  });

  test('lists all errors with links', () => {
    render(
      <ChakraWrapper>
        <FormErrorSummary errors={errors} />
      </ChakraWrapper>
    );

    expect(screen.getByText(/email: email is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password: password must be at least 8 characters/i)).toBeInTheDocument();
  });

  test('has alert role for screen readers', () => {
    render(
      <ChakraWrapper>
        <FormErrorSummary errors={errors} />
      </ChakraWrapper>
    );

    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
  });

  test('does not render when no errors', () => {
    const { container } = render(
      <ChakraWrapper>
        <FormErrorSummary errors={[]} />
      </ChakraWrapper>
    );

    expect(container.firstChild).toBeNull();
  });

  test('has no accessibility violations', async () => {
    const { container } = render(
      <ChakraWrapper>
        <FormErrorSummary errors={errors} />
      </ChakraWrapper>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test('error links focus fields when clicked', async () => {
    const user = userEvent.setup();
    const mockField = document.createElement('input');
    mockField.id = 'email';
    document.body.appendChild(mockField);

    render(
      <ChakraWrapper>
        <FormErrorSummary errors={errors} />
      </ChakraWrapper>
    );

    const errorLink = screen.getByText(/email: email is required/i);
    await user.click(errorLink);

    expect(mockField).toHaveFocus();

    document.body.removeChild(mockField);
  });
});

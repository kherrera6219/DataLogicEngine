import React, { useState, useId } from 'react';
import {
  FormControl,
  FormLabel,
  FormErrorMessage,
  FormHelperText,
  Input,
  Textarea,
  Select,
  Checkbox,
  Radio,
  RadioGroup,
  Stack,
  Box
} from '@chakra-ui/react';
import { LiveRegion, AlertRegion } from './LiveRegion';

/**
 * Accessible Form Field
 * Implements WCAG 2.2 Level AA form accessibility requirements
 *
 * Features:
 * - Programmatic label association
 * - Error message announcements
 * - Helper text for context
 * - Required field indicators
 * - ARIA attributes for validation states
 *
 * @param {string} label - Field label
 * @param {string} error - Error message
 * @param {string} helperText - Helper text
 * @param {boolean} required - Whether field is required
 * @param {string} type - Input type
 */
export function AccessibleFormField({
  label,
  error,
  helperText,
  required = false,
  type = 'text',
  name,
  value,
  onChange,
  placeholder,
  disabled = false,
  ...props
}) {
  const fieldId = useId();
  const errorId = `${fieldId}-error`;
  const helperId = `${fieldId}-helper`;

  const ariaDescribedBy = [
    error ? errorId : null,
    helperText ? helperId : null
  ].filter(Boolean).join(' ');

  return (
    <FormControl
      isInvalid={!!error}
      isRequired={required}
      isDisabled={disabled}
    >
      <FormLabel htmlFor={fieldId}>
        {label}
        {required && (
          <Box
            as="span"
            color="red.500"
            ml={1}
            aria-label="required"
          >
            *
          </Box>
        )}
      </FormLabel>

      <Input
        id={fieldId}
        name={name}
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        aria-describedby={ariaDescribedBy || undefined}
        aria-invalid={!!error}
        aria-required={required}
        {...props}
      />

      {helperText && (
        <FormHelperText id={helperId}>
          {helperText}
        </FormHelperText>
      )}

      {error && (
        <>
          <FormErrorMessage id={errorId} role="alert">
            {error}
          </FormErrorMessage>
          <AlertRegion>
            {`${label}: ${error}`}
          </AlertRegion>
        </>
      )}
    </FormControl>
  );
}

/**
 * Accessible Textarea Field
 */
export function AccessibleTextarea({
  label,
  error,
  helperText,
  required = false,
  name,
  value,
  onChange,
  placeholder,
  disabled = false,
  rows = 4,
  ...props
}) {
  const fieldId = useId();
  const errorId = `${fieldId}-error`;
  const helperId = `${fieldId}-helper`;
  const charCountId = `${fieldId}-charcount`;

  const maxLength = props.maxLength;
  const charCount = value?.length || 0;
  const remaining = maxLength ? maxLength - charCount : null;

  const ariaDescribedBy = [
    error ? errorId : null,
    helperText ? helperId : null,
    maxLength ? charCountId : null
  ].filter(Boolean).join(' ');

  return (
    <FormControl
      isInvalid={!!error}
      isRequired={required}
      isDisabled={disabled}
    >
      <FormLabel htmlFor={fieldId}>
        {label}
        {required && <Box as="span" color="red.500" ml={1}>*</Box>}
      </FormLabel>

      <Textarea
        id={fieldId}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        rows={rows}
        aria-describedby={ariaDescribedBy || undefined}
        aria-invalid={!!error}
        aria-required={required}
        {...props}
      />

      {helperText && (
        <FormHelperText id={helperId}>
          {helperText}
        </FormHelperText>
      )}

      {maxLength && (
        <FormHelperText id={charCountId} textAlign="right">
          <span aria-live="polite">
            {remaining} characters remaining
          </span>
        </FormHelperText>
      )}

      {error && (
        <>
          <FormErrorMessage id={errorId} role="alert">
            {error}
          </FormErrorMessage>
          <AlertRegion>
            {`${label}: ${error}`}
          </AlertRegion>
        </>
      )}
    </FormControl>
  );
}

/**
 * Accessible Select Field
 */
export function AccessibleSelect({
  label,
  error,
  helperText,
  required = false,
  name,
  value,
  onChange,
  placeholder,
  disabled = false,
  options = [],
  ...props
}) {
  const fieldId = useId();
  const errorId = `${fieldId}-error`;
  const helperId = `${fieldId}-helper`;

  const ariaDescribedBy = [
    error ? errorId : null,
    helperText ? helperId : null
  ].filter(Boolean).join(' ');

  return (
    <FormControl
      isInvalid={!!error}
      isRequired={required}
      isDisabled={disabled}
    >
      <FormLabel htmlFor={fieldId}>
        {label}
        {required && <Box as="span" color="red.500" ml={1}>*</Box>}
      </FormLabel>

      <Select
        id={fieldId}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        aria-describedby={ariaDescribedBy || undefined}
        aria-invalid={!!error}
        aria-required={required}
        {...props}
      >
        {options.map((option, index) => (
          <option key={index} value={option.value}>
            {option.label}
          </option>
        ))}
      </Select>

      {helperText && (
        <FormHelperText id={helperId}>
          {helperText}
        </FormHelperText>
      )}

      {error && (
        <>
          <FormErrorMessage id={errorId} role="alert">
            {error}
          </FormErrorMessage>
          <AlertRegion>
            {`${label}: ${error}`}
          </AlertRegion>
        </>
      )}
    </FormControl>
  );
}

/**
 * Accessible Checkbox Field
 */
export function AccessibleCheckbox({
  label,
  error,
  helperText,
  required = false,
  name,
  checked,
  onChange,
  disabled = false,
  ...props
}) {
  const fieldId = useId();
  const errorId = `${fieldId}-error`;
  const helperId = `${fieldId}-helper`;

  const ariaDescribedBy = [
    error ? errorId : null,
    helperText ? helperId : null
  ].filter(Boolean).join(' ');

  return (
    <FormControl
      isInvalid={!!error}
      isRequired={required}
      isDisabled={disabled}
    >
      <Checkbox
        id={fieldId}
        name={name}
        isChecked={checked}
        onChange={onChange}
        aria-describedby={ariaDescribedBy || undefined}
        aria-invalid={!!error}
        aria-required={required}
        {...props}
      >
        {label}
        {required && <Box as="span" color="red.500" ml={1}>*</Box>}
      </Checkbox>

      {helperText && (
        <FormHelperText id={helperId} ml={6}>
          {helperText}
        </FormHelperText>
      )}

      {error && (
        <>
          <FormErrorMessage id={errorId} role="alert" ml={6}>
            {error}
          </FormErrorMessage>
          <AlertRegion>
            {`${label}: ${error}`}
          </AlertRegion>
        </>
      )}
    </FormControl>
  );
}

/**
 * Form Validation Error Summary
 * WCAG 2.2 Level A - Error Identification (3.3.1)
 * Provides a summary of all form errors at the top of the form
 */
export function FormErrorSummary({ errors = [], onErrorClick }) {
  if (!errors || errors.length === 0) return null;

  return (
    <Box
      role="alert"
      aria-labelledby="error-summary-heading"
      bg="red.50"
      borderWidth="2px"
      borderColor="red.500"
      borderRadius="md"
      p={4}
      mb={6}
    >
      <Box
        as="h2"
        id="error-summary-heading"
        fontSize="lg"
        fontWeight="bold"
        color="red.700"
        mb={3}
      >
        There {errors.length === 1 ? 'is' : 'are'} {errors.length} error{errors.length > 1 ? 's' : ''} in this form
      </Box>
      <Box as="ul" listStyleType="disc" pl={5}>
        {errors.map((error, index) => (
          <Box as="li" key={index} mb={2}>
            <Box
              as="a"
              href={`#${error.fieldId}`}
              color="red.700"
              textDecoration="underline"
              onClick={(e) => {
                e.preventDefault();
                if (onErrorClick) {
                  onErrorClick(error.fieldId);
                } else {
                  document.getElementById(error.fieldId)?.focus();
                }
              }}
              _hover={{ color: 'red.900' }}
            >
              {error.label}: {error.message}
            </Box>
          </Box>
        ))}
      </Box>
      <AlertRegion>
        {`Form has ${errors.length} error${errors.length > 1 ? 's' : ''}. Please review and correct.`}
      </AlertRegion>
    </Box>
  );
}

export default AccessibleFormField;

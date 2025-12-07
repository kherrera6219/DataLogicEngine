import React from 'react';
import { Box } from '@chakra-ui/react';

/**
 * Visually Hidden Component
 * Screen-reader only text (sr-only pattern)
 * Hides content visually but keeps it accessible to assistive technologies
 *
 * Use cases:
 * - Icon button labels
 * - Additional context for screen readers
 * - Skip links
 * - Form labels that are visually redundant
 *
 * @param {ReactNode} children - Content to hide visually
 * @param {boolean} focusable - Whether element should be visible when focused
 */
export function VisuallyHidden({ children, focusable = false, as = 'span' }) {
  const styles = {
    position: 'absolute',
    width: '1px',
    height: '1px',
    padding: 0,
    margin: '-1px',
    overflow: 'hidden',
    clip: 'rect(0, 0, 0, 0)',
    whiteSpace: 'nowrap',
    border: 0
  };

  const focusableStyles = focusable
    ? {
        _focus: {
          position: 'static',
          width: 'auto',
          height: 'auto',
          padding: 'inherit',
          margin: 'inherit',
          overflow: 'visible',
          clip: 'auto',
          whiteSpace: 'normal'
        }
      }
    : {};

  return (
    <Box as={as} sx={styles} {...focusableStyles}>
      {children}
    </Box>
  );
}

export default VisuallyHidden;

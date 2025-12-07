import React from 'react';
import { Box, Link } from '@chakra-ui/react';

/**
 * Skip Navigation Link
 * WCAG 2.2 Level A requirement - Bypass Blocks (2.4.1)
 * Allows keyboard users to skip repetitive navigation
 *
 * @param {string} href - Target element ID (e.g., "#main-content")
 * @param {string} children - Link text
 */
export function SkipLink({ href = '#main-content', children = 'Skip to main content' }) {
  const handleClick = (e) => {
    e.preventDefault();
    const target = document.querySelector(href);
    if (target) {
      target.focus();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  return (
    <Link
      href={href}
      onClick={handleClick}
      position="absolute"
      left="-9999px"
      zIndex={9999}
      padding="0.5rem 1rem"
      bg="blue.600"
      color="white"
      fontWeight="bold"
      textDecoration="none"
      borderRadius="md"
      _focus={{
        left: '0.5rem',
        top: '0.5rem',
        outline: '3px solid',
        outlineColor: 'blue.300',
        outlineOffset: '2px'
      }}
      sx={{
        '&:focus': {
          left: '0.5rem !important',
          top: '0.5rem !important'
        }
      }}
    >
      {children}
    </Link>
  );
}

/**
 * Skip Links Container - Multiple skip links for complex pages
 */
export function SkipLinks({ links = [] }) {
  const defaultLinks = [
    { href: '#main-content', text: 'Skip to main content' },
    { href: '#navigation', text: 'Skip to navigation' },
    { href: '#footer', text: 'Skip to footer' }
  ];

  const skipLinks = links.length > 0 ? links : defaultLinks;

  return (
    <Box as="nav" aria-label="Skip navigation">
      {skipLinks.map((link, index) => (
        <SkipLink key={index} href={link.href}>
          {link.text}
        </SkipLink>
      ))}
    </Box>
  );
}

export default SkipLink;

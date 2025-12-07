/**
 * Test Utilities for Accessibility Testing
 * Provides helpers for testing components with accessibility checks
 */

import React from 'react';
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { ChakraProvider } from '@chakra-ui/react';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

/**
 * Custom render function that wraps components with providers
 */
export function renderWithProviders(ui, options = {}) {
  const Wrapper = ({ children }) => (
    <ChakraProvider>{children}</ChakraProvider>
  );

  return render(ui, { wrapper: Wrapper, ...options });
}

/**
 * Test component for accessibility violations
 * @param {ReactElement} component - Component to test
 * @param {Object} options - axe-core options
 * @returns {Promise<Object>} - Accessibility test results
 */
export async function testAccessibility(component, options = {}) {
  const { container } = renderWithProviders(component);
  const results = await axe(container, {
    rules: {
      // Configure specific rules if needed
      'color-contrast': { enabled: true },
      'label': { enabled: true },
      'button-name': { enabled: true },
      'link-name': { enabled: true },
      'image-alt': { enabled: true },
      ...options.rules
    }
  });

  return results;
}

/**
 * Assert that a component has no accessibility violations
 * Usage in tests:
 * const results = await testAccessibility(<MyComponent />);
 * expect(results).toHaveNoViolations();
 */
export async function expectNoA11yViolations(component, options = {}) {
  const results = await testAccessibility(component, options);
  expect(results).toHaveNoViolations();
}

/**
 * Test keyboard navigation
 * @param {HTMLElement} element - Element to test
 * @param {string} key - Key to press
 */
export function pressKey(element, key, options = {}) {
  const event = new KeyboardEvent('keydown', {
    key,
    bubbles: true,
    cancelable: true,
    ...options
  });
  element.dispatchEvent(event);
}

/**
 * Test Tab key navigation
 */
export function pressTab(element, shift = false) {
  pressKey(element, 'Tab', { shiftKey: shift });
}

/**
 * Test Enter key
 */
export function pressEnter(element) {
  pressKey(element, 'Enter');
}

/**
 * Test Escape key
 */
export function pressEscape(element) {
  pressKey(element, 'Escape');
}

/**
 * Get all focusable elements within a container
 */
export function getFocusableElements(container) {
  return container.querySelectorAll(
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
  );
}

/**
 * Test focus trap - ensures focus stays within container
 */
export function testFocusTrap(container) {
  const focusableElements = getFocusableElements(container);
  const firstElement = focusableElements[0];
  const lastElement = focusableElements[focusableElements.length - 1];

  return {
    firstElement,
    lastElement,
    focusableCount: focusableElements.length,
    // Test that tab from last element cycles to first
    testForwardCycle: () => {
      lastElement.focus();
      pressTab(lastElement);
      return document.activeElement === firstElement;
    },
    // Test that shift+tab from first element cycles to last
    testBackwardCycle: () => {
      firstElement.focus();
      pressTab(firstElement, true);
      return document.activeElement === lastElement;
    }
  };
}

/**
 * Wait for element to be announced to screen reader
 * Checks for aria-live regions
 */
export function waitForAnnouncement(container, timeout = 1000) {
  return new Promise((resolve) => {
    const liveRegions = container.querySelectorAll('[aria-live]');
    if (liveRegions.length === 0) {
      resolve([]);
      return;
    }

    const observer = new MutationObserver((mutations) => {
      const announcements = mutations
        .filter(m => m.type === 'childList' || m.type === 'characterData')
        .map(m => m.target.textContent);

      if (announcements.length > 0) {
        observer.disconnect();
        resolve(announcements);
      }
    });

    liveRegions.forEach(region => {
      observer.observe(region, {
        childList: true,
        characterData: true,
        subtree: true
      });
    });

    setTimeout(() => {
      observer.disconnect();
      resolve([]);
    }, timeout);
  });
}

/**
 * Check if element is visually hidden but accessible to screen readers
 */
export function isVisuallyHidden(element) {
  const style = window.getComputedStyle(element);
  return (
    style.position === 'absolute' &&
    style.width === '1px' &&
    style.height === '1px' &&
    style.overflow === 'hidden'
  );
}

/**
 * Assert element is accessible to screen readers
 */
export function assertAccessibleLabel(element, expectedLabel) {
  const label =
    element.getAttribute('aria-label') ||
    element.getAttribute('aria-labelledby') &&
      document.getElementById(element.getAttribute('aria-labelledby'))?.textContent ||
    element.textContent;

  expect(label).toBe(expectedLabel);
}

export { render, renderWithProviders as default };

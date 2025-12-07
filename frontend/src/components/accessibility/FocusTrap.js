import React, { useEffect, useRef } from 'react';

/**
 * Focus Trap Component
 * Traps keyboard focus within a container (essential for modals and dialogs)
 * WCAG 2.2 Level A requirement - Keyboard (2.1.1)
 *
 * @param {boolean} active - Whether the focus trap is active
 * @param {function} onEscape - Callback when Escape key is pressed
 * @param {ReactNode} children - Child elements
 */
export function FocusTrap({ active = true, onEscape, children, initialFocusRef }) {
  const containerRef = useRef(null);
  const previousActiveElement = useRef(null);

  useEffect(() => {
    if (!active) return;

    // Store the element that had focus before the trap activated
    previousActiveElement.current = document.activeElement;

    const container = containerRef.current;
    if (!container) return;

    // Get all focusable elements
    const focusableElements = container.querySelectorAll(
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    // Focus initial element or first focusable element
    const focusElement = initialFocusRef?.current || firstElement;
    if (focusElement) {
      // Use setTimeout to ensure element is rendered
      setTimeout(() => {
        focusElement.focus();
      }, 0);
    }

    const handleKeyDown = (e) => {
      // Handle Escape key
      if (e.key === 'Escape' && onEscape) {
        onEscape();
        return;
      }

      // Handle Tab key for focus trapping
      if (e.key === 'Tab') {
        if (focusableElements.length === 0) {
          e.preventDefault();
          return;
        }

        if (e.shiftKey) {
          // Shift + Tab - moving backwards
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          // Tab - moving forwards
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);

    // Cleanup function
    return () => {
      document.removeEventListener('keydown', handleKeyDown);

      // Restore focus to previous element
      if (previousActiveElement.current && previousActiveElement.current.focus) {
        previousActiveElement.current.focus();
      }
    };
  }, [active, onEscape, initialFocusRef]);

  return (
    <div ref={containerRef}>
      {children}
    </div>
  );
}

export default FocusTrap;

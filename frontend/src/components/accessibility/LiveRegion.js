import React, { useEffect, useRef } from 'react';
import { Box } from '@chakra-ui/react';

/**
 * Live Region Component
 * ARIA live regions for dynamic content announcements to screen readers
 * WCAG 2.2 Level A requirement - Status Messages (4.1.3)
 *
 * @param {string} politeness - 'polite' (default), 'assertive', or 'off'
 * @param {boolean} atomic - Whether to announce entire region or just changes
 * @param {string} role - ARIA role (status, alert, log, etc.)
 * @param {ReactNode} children - Content to announce
 */
export function LiveRegion({
  children,
  politeness = 'polite',
  atomic = true,
  role = 'status',
  className = '',
  clearAfterAnnouncement = false,
  clearDelay = 5000
}) {
  const regionRef = useRef(null);

  useEffect(() => {
    if (clearAfterAnnouncement && children) {
      const timer = setTimeout(() => {
        if (regionRef.current) {
          regionRef.current.textContent = '';
        }
      }, clearDelay);

      return () => clearTimeout(timer);
    }
  }, [children, clearAfterAnnouncement, clearDelay]);

  return (
    <Box
      ref={regionRef}
      role={role}
      aria-live={politeness}
      aria-atomic={atomic}
      className={`sr-only ${className}`}
      position="absolute"
      left="-10000px"
      width="1px"
      height="1px"
      overflow="hidden"
    >
      {children}
    </Box>
  );
}

/**
 * Alert Live Region - For important, time-sensitive information
 */
export function AlertRegion({ children, className }) {
  return (
    <LiveRegion
      politeness="assertive"
      role="alert"
      atomic={true}
      className={className}
    >
      {children}
    </LiveRegion>
  );
}

/**
 * Status Live Region - For status messages and notifications
 */
export function StatusRegion({ children, className }) {
  return (
    <LiveRegion
      politeness="polite"
      role="status"
      atomic={true}
      className={className}
    >
      {children}
    </LiveRegion>
  );
}

/**
 * Log Live Region - For chat messages, logs, or sequential updates
 */
export function LogRegion({ children, className }) {
  return (
    <LiveRegion
      politeness="polite"
      role="log"
      atomic={false}
      className={className}
    >
      {children}
    </LiveRegion>
  );
}

export default LiveRegion;

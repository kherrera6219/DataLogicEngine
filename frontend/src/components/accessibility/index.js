/**
 * Accessibility Components - Central Export
 * Industry-standard accessible components for WCAG 2.2 AA/AAA compliance
 */

// Error Boundaries
export { default as ErrorBoundary } from '../ErrorBoundary';
export { default as PageErrorBoundary } from '../PageErrorBoundary';

// Navigation & Focus
export { SkipLink, SkipLinks } from './SkipLink';
export { FocusTrap } from './FocusTrap';
export { default as useKeyboardShortcuts, KeyboardShortcutsHelp } from './KeyboardShortcuts';

// Screen Reader Support
export {
  LiveRegion,
  AlertRegion,
  StatusRegion,
  LogRegion
} from './LiveRegion';
export { VisuallyHidden } from './VisuallyHidden';

// Forms
export {
  AccessibleFormField,
  AccessibleTextarea,
  AccessibleSelect,
  AccessibleCheckbox,
  FormErrorSummary
} from './AccessibleForm';

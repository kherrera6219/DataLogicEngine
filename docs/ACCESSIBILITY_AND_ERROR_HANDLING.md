# Accessibility & Error Handling Guide

## Overview

This document describes the accessibility and error handling features implemented in the DataLogicEngine application to meet industry production standards. The implementation follows **WCAG 2.2 Level AA** guidelines with **AAA** enhancements where applicable.

## Table of Contents

- [Error Handling](#error-handling)
- [Accessibility Features](#accessibility-features)
- [Performance Monitoring](#performance-monitoring)
- [Testing](#testing)
- [Implementation Guide](#implementation-guide)
- [Best Practices](#best-practices)

---

## Error Handling

### 1. React Error Boundaries

Error boundaries prevent JavaScript errors from crashing the entire React application.

#### ErrorBoundary Component

**Location:** `frontend/src/components/ErrorBoundary.js`

**Features:**
- Catches rendering errors, lifecycle errors, and constructor errors
- Logs errors to backend error tracking service
- Provides user-friendly fallback UI
- Offers recovery mechanisms (retry, reload)
- WCAG 2.2 AA compliant error display
- Tracks error count for recurring issues

**Usage:**

```jsx
import ErrorBoundary from '@/components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary
      name="app-boundary"
      onReset={() => console.log('Resetting...')}
      showDetails={process.env.NODE_ENV === 'development'}
    >
      <YourComponents />
    </ErrorBoundary>
  );
}
```

#### PageErrorBoundary Component

**Location:** `frontend/src/components/PageErrorBoundary.js`

**Features:**
- Lighter weight boundary for page-level errors
- Allows navigation to other parts of app
- Provides navigation options (back, home, retry)

**Usage:**

```jsx
import PageErrorBoundary from '@/components/PageErrorBoundary';

function Router() {
  return (
    <Routes>
      <Route path="/" element={
        <PageErrorBoundary>
          <HomePage />
        </PageErrorBoundary>
      } />
    </Routes>
  );
}
```

### 2. Global Error Tracking

**Location:** `frontend/src/utils/errorTracking.js`

**Features:**
- Global error handler for uncaught errors
- Unhandled promise rejection handler
- Structured error logging
- Error deduplication (prevents duplicate logs)
- Rate limiting (max 10 errors/minute)
- Integration-ready for Sentry, DataDog, etc.

**Initialization:**

```jsx
import { initializeErrorTracking } from '@/utils/errorTracking';

// In your app entry point (index.js or App.js)
initializeErrorTracking();
```

**Manual Error Logging:**

```jsx
import { logError } from '@/utils/errorTracking';

try {
  // Your code
} catch (error) {
  logError(error, {
    severity: 'error',
    context: 'user-action',
    userId: currentUser.id
  });
}
```

### 3. Backend Error Logging

**Location:** `backend/api.py` (line 514-566)

**Endpoint:** `POST /api/log-error`

**Features:**
- Centralized frontend error logging
- Severity-based logging (critical, error, warning, info)
- Integration-ready for external monitoring services
- Prevents error loops with fail-safe responses

**Request Format:**

```json
{
  "type": "error",
  "message": "Failed to load user data",
  "stack": "Error: Failed to load user data\n    at...",
  "url": "https://app.example.com/dashboard",
  "userAgent": "Mozilla/5.0...",
  "severity": "error",
  "timestamp": "2025-12-07T10:30:00.000Z"
}
```

---

## Accessibility Features

### 1. Skip Navigation Links

**Location:** `frontend/src/components/accessibility/SkipLink.js`

**WCAG:** Level A - Bypass Blocks (2.4.1)

**Features:**
- Allows keyboard users to skip repetitive navigation
- Hidden until focused (visible on Tab)
- Smooth scrolling to target
- High contrast focus indicator

**Usage:**

```jsx
import { SkipLinks } from '@/components/accessibility';

function Layout() {
  return (
    <>
      <SkipLinks links={[
        { href: '#main-content', text: 'Skip to main content' },
        { href: '#navigation', text: 'Skip to navigation' }
      ]} />
      <nav id="navigation">...</nav>
      <main id="main-content" tabIndex="-1">...</main>
    </>
  );
}
```

### 2. Focus Trap

**Location:** `frontend/src/components/accessibility/FocusTrap.js`

**WCAG:** Level A - Keyboard (2.1.1)

**Features:**
- Traps keyboard focus within modals/dialogs
- Handles Tab and Shift+Tab navigation
- Supports Escape key to close
- Restores focus to previous element on close

**Usage:**

```jsx
import { FocusTrap } from '@/components/accessibility';

function Modal({ isOpen, onClose }) {
  return isOpen && (
    <FocusTrap active={isOpen} onEscape={onClose}>
      <div role="dialog" aria-modal="true">
        <h2>Modal Title</h2>
        <button onClick={onClose}>Close</button>
      </div>
    </FocusTrap>
  );
}
```

### 3. ARIA Live Regions

**Location:** `frontend/src/components/accessibility/LiveRegion.js`

**WCAG:** Level A - Status Messages (4.1.3)

**Features:**
- Announces dynamic content to screen readers
- Multiple politeness levels (polite, assertive)
- Specialized regions (alert, status, log)
- Auto-clear after announcement option

**Usage:**

```jsx
import { AlertRegion, StatusRegion } from '@/components/accessibility';

function Notifications() {
  const [message, setMessage] = useState('');

  return (
    <>
      {/* For critical alerts */}
      <AlertRegion>{errorMessage}</AlertRegion>

      {/* For status updates */}
      <StatusRegion>{statusMessage}</StatusRegion>
    </>
  );
}
```

### 4. Visually Hidden Content

**Location:** `frontend/src/components/accessibility/VisuallyHidden.js`

**Features:**
- Screen-reader only text (sr-only pattern)
- Hides content visually but keeps it accessible
- Optional focus-visible variant

**Usage:**

```jsx
import { VisuallyHidden } from '@/components/accessibility';

function IconButton() {
  return (
    <button>
      <SearchIcon />
      <VisuallyHidden>Search</VisuallyHidden>
    </button>
  );
}
```

### 5. Keyboard Shortcuts

**Location:** `frontend/src/components/accessibility/KeyboardShortcuts.js`

**WCAG:** Level AAA - Help (3.3.5)

**Features:**
- Customizable keyboard shortcuts
- Help modal (press `?` to view)
- Supports Ctrl, Shift, Alt modifiers
- Prevents conflicts with browser shortcuts

**Usage:**

```jsx
import useKeyboardShortcuts, { KeyboardShortcutsHelp }
  from '@/components/accessibility/KeyboardShortcuts';

function App() {
  useKeyboardShortcuts({
    'ctrl+k': () => openSearch(),
    'ctrl+/': () => toggleSidebar(),
    'escape': () => closeModal()
  });

  return (
    <>
      <YourApp />
      <KeyboardShortcutsHelp shortcuts={[
        { keys: ['Ctrl+K'], description: 'Open search' },
        { keys: ['Ctrl+/'], description: 'Toggle sidebar' }
      ]} />
    </>
  );
}
```

### 6. Accessible Forms

**Location:** `frontend/src/components/accessibility/AccessibleForm.js`

**WCAG:** Level AA - Multiple criteria

**Features:**
- Programmatic label association
- Error message announcements via ARIA live regions
- Required field indicators
- Helper text for context
- Character count for textareas
- Form error summary

**Usage:**

```jsx
import {
  AccessibleFormField,
  AccessibleTextarea,
  AccessibleSelect,
  AccessibleCheckbox,
  FormErrorSummary
} from '@/components/accessibility';

function SignUpForm() {
  const [errors, setErrors] = useState([]);

  return (
    <form onSubmit={handleSubmit}>
      <FormErrorSummary errors={errors} />

      <AccessibleFormField
        label="Email"
        name="email"
        type="email"
        value={email}
        onChange={setEmail}
        error={emailError}
        required
        helperText="We'll never share your email"
      />

      <AccessibleTextarea
        label="Bio"
        name="bio"
        value={bio}
        onChange={setBio}
        maxLength={500}
        helperText="Tell us about yourself"
      />

      <AccessibleSelect
        label="Country"
        name="country"
        value={country}
        onChange={setCountry}
        options={countries}
        required
      />

      <AccessibleCheckbox
        label="I agree to the terms"
        name="terms"
        checked={agreedToTerms}
        onChange={setAgreedToTerms}
        required
      />

      <button type="submit">Sign Up</button>
    </form>
  );
}
```

---

## Performance Monitoring

**Location:** `frontend/src/utils/performanceMonitoring.js`

**Features:**
- Core Web Vitals tracking (LCP, FID, CLS, FCP, TTFB, INP)
- Long task detection (>50ms)
- Resource loading performance
- Custom performance marks and measures
- Automatic rating (good, needs-improvement, poor)
- Integration-ready for analytics services

**Initialization:**

```jsx
import { initializePerformanceMonitoring } from '@/utils/performanceMonitoring';

// In your app entry point
initializePerformanceMonitoring();
```

**Custom Performance Tracking:**

```jsx
import { mark, measure } from '@/utils/performanceMonitoring';

function loadData() {
  mark('data-load-start');

  await fetchData();

  mark('data-load-end');
  const duration = measure('data-load', 'data-load-start', 'data-load-end');
  console.log(`Data loaded in ${duration}ms`);
}
```

**Get Performance Summary:**

```jsx
import { getPerformanceSummary } from '@/utils/performanceMonitoring';

const summary = getPerformanceSummary();
console.log('LCP:', summary.vitals.LCP.value, summary.vitals.LCP.rating);
console.log('FID:', summary.vitals.FID.value, summary.vitals.FID.rating);
console.log('CLS:', summary.vitals.CLS.value, summary.vitals.CLS.rating);
```

---

## Testing

### 1. Accessibility Testing Setup

**Location:** `frontend/src/utils/setupTests.js`

**Features:**
- Jest and React Testing Library configuration
- jest-axe integration for automated accessibility testing
- Mock implementations for browser APIs

### 2. Test Utilities

**Location:** `frontend/src/utils/testUtils.js`

**Features:**
- `testAccessibility()` - Run axe accessibility tests
- `expectNoA11yViolations()` - Assert no violations
- `pressTab()`, `pressEnter()`, `pressEscape()` - Keyboard testing
- `testFocusTrap()` - Test focus trapping
- `waitForAnnouncement()` - Test ARIA live regions
- `assertAccessibleLabel()` - Test accessible labels

**Example Test:**

```jsx
import { render, screen } from '@testing-library/react';
import { axe } from 'jest-axe';
import { expectNoA11yViolations } from '@/utils/testUtils';

test('MyComponent has no accessibility violations', async () => {
  const { container } = render(<MyComponent />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### 3. Running Tests

```bash
# Run all tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test ErrorBoundary.test.js

# Run tests in watch mode
npm test -- --watch
```

---

## Implementation Guide

### Adding Error Boundaries to Your App

1. **Wrap entire app:**

```jsx
// frontend/src/index.js
import ErrorBoundary from './components/ErrorBoundary';
import { initializeErrorTracking } from './utils/errorTracking';

initializeErrorTracking();

ReactDOM.render(
  <ErrorBoundary name="root">
    <App />
  </ErrorBoundary>,
  document.getElementById('root')
);
```

2. **Wrap individual routes:**

```jsx
// frontend/src/App.js
import PageErrorBoundary from './components/PageErrorBoundary';

function App() {
  return (
    <Routes>
      <Route path="/dashboard" element={
        <PageErrorBoundary>
          <DashboardPage />
        </PageErrorBoundary>
      } />
    </Routes>
  );
}
```

### Adding Accessibility to Existing Pages

1. **Add skip navigation:**

```jsx
import { SkipLinks } from './components/accessibility';

function Layout() {
  return (
    <>
      <SkipLinks />
      <nav id="navigation">...</nav>
      <main id="main-content" tabIndex="-1">...</main>
    </>
  );
}
```

2. **Add ARIA landmarks:**

```jsx
<header role="banner">
  <nav role="navigation" aria-label="Main navigation">...</nav>
</header>

<main role="main" id="main-content">
  <section aria-labelledby="section-heading">
    <h2 id="section-heading">Section Title</h2>
  </section>
</main>

<aside role="complementary" aria-label="Related content">...</aside>

<footer role="contentinfo">...</footer>
```

3. **Update forms:**

Replace standard form inputs with accessible components:

```jsx
// Before
<input type="text" placeholder="Email" />

// After
<AccessibleFormField
  label="Email"
  name="email"
  type="email"
  value={email}
  onChange={setEmail}
  required
/>
```

4. **Add live regions for notifications:**

```jsx
import { StatusRegion } from './components/accessibility';

function NotificationSystem() {
  return (
    <>
      {/* Visual notification */}
      <Toast message={message} />

      {/* Screen reader announcement */}
      <StatusRegion>{message}</StatusRegion>
    </>
  );
}
```

---

## Best Practices

### Error Handling

1. **Always log errors** - Use `logError()` for all caught errors
2. **Provide context** - Include relevant user/action context
3. **Don't over-log** - Rate limiting prevents log spam
4. **Test error states** - Test both happy and error paths
5. **User-friendly messages** - Show helpful error messages, not stack traces

### Accessibility

1. **Test with keyboard** - Ensure all functionality works without mouse
2. **Use semantic HTML** - Use `<button>`, `<nav>`, `<main>`, etc.
3. **Label everything** - All interactive elements need accessible labels
4. **Test with screen reader** - Use NVDA (Windows) or VoiceOver (Mac)
5. **Maintain focus order** - Logical tab order matches visual order
6. **Color contrast** - Minimum 4.5:1 for normal text, 3:1 for large text
7. **Don't rely on color alone** - Use icons, text, or patterns too
8. **Provide text alternatives** - Alt text for images, labels for icons
9. **Support zoom** - Design works at 200% zoom
10. **Test automated tools** - Run jest-axe on all components

### Performance

1. **Monitor Web Vitals** - Track LCP, FID, CLS regularly
2. **Optimize long tasks** - Break up work >50ms
3. **Lazy load** - Code split and lazy load routes/components
4. **Optimize images** - Use modern formats (WebP), lazy loading
5. **Cache effectively** - Use service workers, browser caching

---

## WCAG 2.2 Compliance Checklist

### Level A (Minimum)

- ✅ 1.1.1 Non-text Content - All images have alt text
- ✅ 2.1.1 Keyboard - All functionality available via keyboard
- ✅ 2.4.1 Bypass Blocks - Skip navigation links provided
- ✅ 3.3.1 Error Identification - Form errors clearly identified
- ✅ 4.1.1 Parsing - Valid HTML structure
- ✅ 4.1.2 Name, Role, Value - All UI components have accessible names

### Level AA (Target)

- ✅ 1.4.3 Contrast - Minimum 4.5:1 contrast ratio
- ✅ 2.4.6 Headings and Labels - Descriptive headings and labels
- ✅ 2.4.7 Focus Visible - Keyboard focus indicator visible
- ✅ 3.2.4 Consistent Identification - Consistent component behavior
- ✅ 3.3.3 Error Suggestion - Form errors provide suggestions
- ✅ 3.3.4 Error Prevention - Confirmation for critical actions
- ✅ 4.1.3 Status Messages - Live regions for status updates

### Level AAA (Enhanced)

- ✅ 2.4.8 Location - User knows where they are in the site
- ✅ 3.3.5 Help - Context-sensitive help available (keyboard shortcuts guide)

---

## Resources

### Documentation
- [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)
- [MDN Accessibility](https://developer.mozilla.org/en-US/docs/Web/Accessibility)
- [React Accessibility](https://react.dev/learn/accessibility)
- [Jest-axe Documentation](https://github.com/nickcolley/jest-axe)

### Testing Tools
- [axe DevTools](https://www.deque.com/axe/devtools/) - Browser extension
- [WAVE](https://wave.webaim.org/) - Web accessibility evaluation tool
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) - Chrome DevTools
- [NVDA](https://www.nvaccess.org/) - Free screen reader (Windows)
- [VoiceOver](https://www.apple.com/accessibility/voiceover/) - Built-in screen reader (Mac)

### Performance
- [Web Vitals](https://web.dev/vitals/) - Google's Web Vitals guide
- [WebPageTest](https://www.webpagetest.org/) - Performance testing tool

---

## Support

For questions or issues:
1. Check this documentation
2. Review example tests in `frontend/src/components/__tests__/`
3. Consult [WCAG 2.2 Guidelines](https://www.w3.org/WAI/WCAG22/quickref/)
4. Open an issue on GitHub

---

**Last Updated:** December 7, 2025
**Version:** 1.0.0
**Compliance Level:** WCAG 2.2 Level AA (with AAA enhancements)

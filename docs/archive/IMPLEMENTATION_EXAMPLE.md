# Implementation Example - Complete Integration

This document shows a complete example of integrating all accessibility and error handling features into your application.

## Step 1: Application Entry Point

**File:** `frontend/src/index.js`

```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { ChakraProvider } from '@chakra-ui/react';
import App from './App';
import ErrorBoundary from './components/ErrorBoundary';
import { initializeErrorTracking } from './utils/errorTracking';
import { initializePerformanceMonitoring } from './utils/performanceMonitoring';

// Initialize error tracking and performance monitoring
initializeErrorTracking();
initializePerformanceMonitoring();

const root = ReactDOM.createRoot(document.getElementById('root'));

root.render(
  <React.StrictMode>
    <ErrorBoundary
      name="root-boundary"
      showDetails={process.env.NODE_ENV === 'development'}
    >
      <ChakraProvider>
        <App />
      </ChakraProvider>
    </ErrorBoundary>
  </React.StrictMode>
);
```

## Step 2: Main App Layout with Accessibility

**File:** `frontend/src/App.js`

```jsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Box } from '@chakra-ui/react';
import { SkipLinks } from './components/accessibility';
import { KeyboardShortcutsHelp } from './components/accessibility/KeyboardShortcuts';
import PageErrorBoundary from './components/PageErrorBoundary';
import Navigation from './components/Navigation';
import HomePage from './pages/HomePage';
import DashboardPage from './pages/DashboardPage';
import Footer from './components/Footer';

function App() {
  return (
    <Router>
      <Box minH="100vh" display="flex" flexDirection="column">
        {/* Skip navigation for keyboard users */}
        <SkipLinks links={[
          { href: '#main-content', text: 'Skip to main content' },
          { href: '#navigation', text: 'Skip to navigation' }
        ]} />

        {/* Main navigation with ARIA landmarks */}
        <Box as="header" role="banner">
          <Navigation id="navigation" />
        </Box>

        {/* Main content area */}
        <Box
          as="main"
          role="main"
          id="main-content"
          tabIndex="-1"
          flex="1"
          p={4}
        >
          <Routes>
            <Route path="/" element={
              <PageErrorBoundary>
                <HomePage />
              </PageErrorBoundary>
            } />

            <Route path="/dashboard" element={
              <PageErrorBoundary>
                <DashboardPage />
              </PageErrorBoundary>
            } />
          </Routes>
        </Box>

        {/* Footer */}
        <Box as="footer" role="contentinfo">
          <Footer />
        </Box>

        {/* Keyboard shortcuts help (press ? to view) */}
        <KeyboardShortcutsHelp shortcuts={[
          { keys: ['/', 'Ctrl+K'], description: 'Focus search' },
          { keys: ['g h'], description: 'Go to home' },
          { keys: ['g d'], description: 'Go to dashboard' }
        ]} />
      </Box>
    </Router>
  );
}

export default App;
```

## Step 3: Accessible Page Example

**File:** `frontend/src/pages/DashboardPage.js`

```jsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Heading,
  VStack,
  Button,
  useToast,
  Spinner,
  Text
} from '@chakra-ui/react';
import {
  AccessibleFormField,
  FormErrorSummary,
  StatusRegion,
  AlertRegion
} from '../components/accessibility';
import { logError } from '../utils/errorTracking';
import { mark, measure } from '../utils/performanceMonitoring';

function DashboardPage() {
  const [formData, setFormData] = useState({ name: '', email: '' });
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const toast = useToast();

  // Performance monitoring
  useEffect(() => {
    mark('dashboard-load-start');

    // Simulate data loading
    setTimeout(() => {
      mark('dashboard-load-end');
      const loadTime = measure(
        'dashboard-load',
        'dashboard-load-start',
        'dashboard-load-end'
      );
      console.log(`Dashboard loaded in ${loadTime}ms`);
    }, 100);
  }, []);

  const validateForm = () => {
    const newErrors = [];

    if (!formData.name.trim()) {
      newErrors.push({
        fieldId: 'name-field',
        label: 'Name',
        message: 'Name is required'
      });
    }

    if (!formData.email.trim()) {
      newErrors.push({
        fieldId: 'email-field',
        label: 'Email',
        message: 'Email is required'
      });
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.push({
        fieldId: 'email-field',
        label: 'Email',
        message: 'Email is invalid'
      });
    }

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Clear previous messages
    setStatusMessage('');
    setErrorMessage('');

    // Validate form
    if (!validateForm()) {
      setErrorMessage('Please correct the errors in the form');
      return;
    }

    setLoading(true);
    setStatusMessage('Submitting form...');

    try {
      mark('form-submit-start');

      const response = await fetch('/api/dashboard/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      mark('form-submit-end');
      measure('form-submit', 'form-submit-start', 'form-submit-end');

      if (!response.ok) {
        throw new Error('Failed to submit form');
      }

      const data = await response.json();

      // Success
      setStatusMessage('Form submitted successfully!');
      toast({
        title: 'Success',
        description: 'Your information has been updated',
        status: 'success',
        duration: 5000,
        isClosable: true
      });

      // Reset form
      setFormData({ name: '', email: '' });
      setErrors([]);

    } catch (error) {
      // Error handling
      const errorMsg = 'Failed to submit form. Please try again.';
      setErrorMessage(errorMsg);

      // Log error
      logError(error, {
        severity: 'error',
        context: 'dashboard-form-submit',
        formData: { name: formData.name, email: formData.email }
      });

      // Show toast
      toast({
        title: 'Error',
        description: errorMsg,
        status: 'error',
        duration: 7000,
        isClosable: true
      });

    } finally {
      setLoading(false);
    }
  };

  return (
    <Box maxW="800px" mx="auto" py={8}>
      {/* Page heading with ARIA landmark */}
      <VStack spacing={6} align="stretch">
        <Heading as="h1" size="xl" id="page-heading">
          Dashboard
        </Heading>

        <Text color="gray.600">
          Update your profile information
        </Text>

        {/* Form with accessibility features */}
        <Box
          as="form"
          onSubmit={handleSubmit}
          aria-labelledby="page-heading"
          noValidate
        >
          {/* Error summary at top of form */}
          <FormErrorSummary errors={errors} />

          <VStack spacing={4} align="stretch">
            {/* Accessible form fields */}
            <AccessibleFormField
              label="Name"
              name="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              error={errors.find(e => e.fieldId === 'name-field')?.message}
              required
              helperText="Your full name"
            />

            <AccessibleFormField
              label="Email"
              name="email"
              type="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              error={errors.find(e => e.fieldId === 'email-field')?.message}
              required
              helperText="We'll use this email to contact you"
            />

            {/* Submit button with loading state */}
            <Button
              type="submit"
              colorScheme="blue"
              isLoading={loading}
              loadingText="Submitting..."
              aria-label="Submit form"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Spinner size="sm" mr={2} />
                  Submitting...
                </>
              ) : (
                'Submit'
              )}
            </Button>
          </VStack>
        </Box>

        {/* ARIA live regions for screen reader announcements */}
        {statusMessage && (
          <StatusRegion>{statusMessage}</StatusRegion>
        )}

        {errorMessage && (
          <AlertRegion>{errorMessage}</AlertRegion>
        )}
      </VStack>
    </Box>
  );
}

export default DashboardPage;
```

## Step 4: Accessible Modal Example

**File:** `frontend/src/components/SettingsModal.js`

```jsx
import React, { useRef } from 'react';
import {
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  ModalCloseButton,
  Button,
  VStack
} from '@chakra-ui/react';
import { FocusTrap } from './accessibility/FocusTrap';
import { AccessibleCheckbox } from './accessibility/AccessibleForm';

function SettingsModal({ isOpen, onClose }) {
  const [settings, setSettings] = React.useState({
    notifications: true,
    emailUpdates: false,
    darkMode: false
  });

  const closeButtonRef = useRef(null);

  const handleSave = () => {
    // Save settings
    console.log('Saving settings:', settings);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      size="md"
      initialFocusRef={closeButtonRef}
    >
      <ModalOverlay />
      <ModalContent>
        {/* Focus trap ensures keyboard focus stays in modal */}
        <FocusTrap
          active={isOpen}
          onEscape={onClose}
          initialFocusRef={closeButtonRef}
        >
          <ModalHeader id="modal-heading">Settings</ModalHeader>

          <ModalCloseButton
            ref={closeButtonRef}
            aria-label="Close settings dialog"
          />

          <ModalBody>
            <VStack
              spacing={4}
              align="stretch"
              role="group"
              aria-labelledby="modal-heading"
            >
              <AccessibleCheckbox
                label="Enable notifications"
                name="notifications"
                checked={settings.notifications}
                onChange={(e) =>
                  setSettings({ ...settings, notifications: e.target.checked })
                }
                helperText="Receive notifications for important updates"
              />

              <AccessibleCheckbox
                label="Email updates"
                name="emailUpdates"
                checked={settings.emailUpdates}
                onChange={(e) =>
                  setSettings({ ...settings, emailUpdates: e.target.checked })
                }
                helperText="Receive weekly email summaries"
              />

              <AccessibleCheckbox
                label="Dark mode"
                name="darkMode"
                checked={settings.darkMode}
                onChange={(e) =>
                  setSettings({ ...settings, darkMode: e.target.checked })
                }
                helperText="Use dark color scheme"
              />
            </VStack>
          </ModalBody>

          <ModalFooter>
            <Button
              variant="ghost"
              mr={3}
              onClick={onClose}
              aria-label="Cancel and close dialog"
            >
              Cancel
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleSave}
              aria-label="Save settings and close dialog"
            >
              Save
            </Button>
          </ModalFooter>
        </FocusTrap>
      </ModalContent>
    </Modal>
  );
}

export default SettingsModal;
```

## Step 5: Component Testing Example

**File:** `frontend/src/pages/__tests__/DashboardPage.test.js`

```jsx
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { axe } from 'jest-axe';
import { ChakraProvider } from '@chakra-ui/react';
import DashboardPage from '../DashboardPage';

const ChakraWrapper = ({ children }) => (
  <ChakraProvider>{children}</ChakraProvider>
);

describe('DashboardPage', () => {
  test('has no accessibility violations', async () => {
    const { container } = render(
      <ChakraWrapper>
        <DashboardPage />
      </ChakraWrapper>
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  test('displays form error summary when validation fails', async () => {
    const user = userEvent.setup();

    render(
      <ChakraWrapper>
        <DashboardPage />
      </ChakraWrapper>
    );

    // Submit empty form
    const submitButton = screen.getByRole('button', { name: /submit/i });
    await user.click(submitButton);

    // Error summary should appear
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText(/there are 2 errors/i)).toBeInTheDocument();
  });

  test('keyboard navigation works correctly', async () => {
    const user = userEvent.setup();

    render(
      <ChakraWrapper>
        <DashboardPage />
      </ChakraWrapper>
    );

    // Tab through form fields
    await user.tab();
    expect(screen.getByLabelText(/name/i)).toHaveFocus();

    await user.tab();
    expect(screen.getByLabelText(/email/i)).toHaveFocus();

    await user.tab();
    expect(screen.getByRole('button', { name: /submit/i })).toHaveFocus();
  });

  test('announces status messages to screen readers', async () => {
    const user = userEvent.setup();

    render(
      <ChakraWrapper>
        <DashboardPage />
      </ChakraWrapper>
    );

    // Fill form
    await user.type(screen.getByLabelText(/name/i), 'John Doe');
    await user.type(screen.getByLabelText(/email/i), 'john@example.com');

    // Submit
    const submitButton = screen.getByRole('button', { name: /submit/i });
    await user.click(submitButton);

    // Wait for live region announcement
    await waitFor(() => {
      const liveRegion = document.querySelector('[aria-live="polite"]');
      expect(liveRegion).toHaveTextContent(/submitting/i);
    });
  });
});
```

## Summary

This complete implementation demonstrates:

1. ✅ **Error Boundaries** - Root and page-level error catching
2. ✅ **Error Tracking** - Global error handler with backend logging
3. ✅ **Performance Monitoring** - Web Vitals and custom metrics
4. ✅ **Skip Navigation** - Keyboard accessibility
5. ✅ **Focus Management** - Modal focus trap
6. ✅ **ARIA Live Regions** - Screen reader announcements
7. ✅ **Accessible Forms** - Proper labels, error messages, validation
8. ✅ **Keyboard Shortcuts** - Global shortcuts with help modal
9. ✅ **Comprehensive Testing** - Automated accessibility tests
10. ✅ **WCAG 2.2 AA Compliance** - Industry-standard accessibility

All components work together to create a production-ready, accessible, and robust application.

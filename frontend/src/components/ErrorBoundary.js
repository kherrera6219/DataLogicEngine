import React from 'react';
import {
  Box,
  Button,
  Heading,
  Text,
  VStack,
  Container,
  Code,
  useColorModeValue
} from '@chakra-ui/react';
import { WarningIcon } from '@chakra-ui/icons';

/**
 * Error Boundary Component - Catches JavaScript errors anywhere in child component tree
 * Implements industry-standard error handling with user-friendly fallback UI
 *
 * Features:
 * - Catches rendering errors, lifecycle errors, and constructor errors
 * - Logs errors to error tracking service
 * - Provides recovery mechanisms (retry)
 * - Prevents entire app from crashing
 * - WCAG 2.2 AA compliant error display
 *
 * @see https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0
    };
  }

  static getDerivedStateFromError(error) {
    // Update state so the next render will show the fallback UI
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    // Log error to error reporting service
    this.logErrorToService(error, errorInfo);

    // Update state with error details
    this.setState(prevState => ({
      error,
      errorInfo,
      errorCount: prevState.errorCount + 1
    }));

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Error Boundary caught an error:', error, errorInfo);
    }
  }

  logErrorToService = (error, errorInfo) => {
    // Log to backend error tracking
    try {
      fetch('/api/log-error', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error: error.toString(),
          errorInfo: errorInfo.componentStack,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href,
          boundaryName: this.props.name || 'Unknown'
        })
      }).catch(err => {
        console.error('Failed to log error to service:', err);
      });
    } catch (e) {
      console.error('Error logging failed:', e);
    }
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null
    });

    // Call optional onReset callback
    if (this.props.onReset) {
      this.props.onReset();
    }
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    const { hasError, error, errorInfo, errorCount } = this.state;
    const { children, fallback, showDetails = false } = this.props;

    if (hasError) {
      // Custom fallback UI if provided
      if (fallback) {
        return fallback({ error, errorInfo, onReset: this.handleReset });
      }

      // Default fallback UI
      const bgColor = useColorModeValue('gray.50', 'gray.900');
      const borderColor = useColorModeValue('red.200', 'red.700');

      return (
        <Container maxW="container.md" py={8}>
          <Box
            role="alert"
            aria-live="assertive"
            aria-atomic="true"
            bg={bgColor}
            borderWidth="2px"
            borderColor={borderColor}
            borderRadius="lg"
            p={8}
          >
            <VStack spacing={4} align="stretch">
              <Box textAlign="center">
                <WarningIcon
                  w={12}
                  h={12}
                  color="red.500"
                  aria-hidden="true"
                />
              </Box>

              <Heading
                size="lg"
                textAlign="center"
                id="error-heading"
              >
                Something Went Wrong
              </Heading>

              <Text
                textAlign="center"
                color="gray.600"
                aria-describedby="error-heading"
              >
                We're sorry, but something unexpected happened.
                {errorCount > 1 && ` This error has occurred ${errorCount} times.`}
              </Text>

              {showDetails && error && (
                <Box
                  as="details"
                  bg="red.50"
                  p={4}
                  borderRadius="md"
                  borderWidth="1px"
                  borderColor="red.200"
                >
                  <Text as="summary" fontWeight="bold" cursor="pointer" mb={2}>
                    Error Details (for developers)
                  </Text>
                  <Code
                    display="block"
                    whiteSpace="pre-wrap"
                    p={2}
                    fontSize="sm"
                    colorScheme="red"
                  >
                    {error.toString()}
                  </Code>
                  {errorInfo && (
                    <Code
                      display="block"
                      whiteSpace="pre-wrap"
                      p={2}
                      mt={2}
                      fontSize="xs"
                      colorScheme="red"
                    >
                      {errorInfo.componentStack}
                    </Code>
                  )}
                </Box>
              )}

              <VStack spacing={2}>
                <Button
                  colorScheme="blue"
                  onClick={this.handleReset}
                  width="full"
                  aria-label="Try to recover from the error"
                >
                  Try Again
                </Button>
                <Button
                  variant="outline"
                  onClick={this.handleReload}
                  width="full"
                  aria-label="Reload the page"
                >
                  Reload Page
                </Button>
                {this.props.onContactSupport && (
                  <Button
                    variant="ghost"
                    onClick={this.props.onContactSupport}
                    width="full"
                    aria-label="Contact support for help"
                  >
                    Contact Support
                  </Button>
                )}
              </VStack>
            </VStack>
          </Box>
        </Container>
      );
    }

    return children;
  }
}

export default ErrorBoundary;

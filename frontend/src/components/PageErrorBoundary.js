import React from 'react';
import {
  Box,
  Button,
  Heading,
  Text,
  VStack,
  Container,
  useColorModeValue
} from '@chakra-ui/react';
import { WarningTwoIcon } from '@chakra-ui/icons';
import { useNavigate } from 'react-router-dom';

/**
 * Page-Level Error Boundary - Lighter weight boundary for page-level errors
 * Allows navigation to other parts of the app while showing error for affected page
 */
function PageErrorFallback({ error, onReset }) {
  const navigate = useNavigate();
  const bgColor = useColorModeValue('orange.50', 'gray.800');
  const borderColor = useColorModeValue('orange.200', 'orange.700');

  const handleGoHome = () => {
    navigate('/');
    onReset();
  };

  const handleGoBack = () => {
    navigate(-1);
    onReset();
  };

  return (
    <Container maxW="container.md" py={12} role="main">
      <Box
        bg={bgColor}
        borderWidth="2px"
        borderColor={borderColor}
        borderRadius="lg"
        p={8}
        role="alert"
        aria-live="polite"
        aria-atomic="true"
      >
        <VStack spacing={6} align="stretch">
          <Box textAlign="center">
            <WarningTwoIcon
              w={10}
              h={10}
              color="orange.500"
              aria-hidden="true"
            />
          </Box>

          <Heading
            size="md"
            textAlign="center"
            id="page-error-heading"
          >
            This Page Encountered an Error
          </Heading>

          <Text
            textAlign="center"
            color="gray.600"
            aria-describedby="page-error-heading"
          >
            Don't worry - the rest of the application is still working.
            You can try going back or return to the home page.
          </Text>

          {process.env.NODE_ENV === 'development' && error && (
            <Text fontSize="sm" color="red.600" fontFamily="mono">
              {error.toString()}
            </Text>
          )}

          <VStack spacing={2}>
            <Button
              colorScheme="orange"
              onClick={onReset}
              width="full"
              aria-label="Retry loading this page"
            >
              Retry This Page
            </Button>
            <Button
              variant="outline"
              onClick={handleGoBack}
              width="full"
              aria-label="Go back to previous page"
            >
              Go Back
            </Button>
            <Button
              variant="ghost"
              onClick={handleGoHome}
              width="full"
              aria-label="Return to home page"
            >
              Go to Home
            </Button>
          </VStack>
        </VStack>
      </Box>
    </Container>
  );
}

/**
 * Page Error Boundary - Wraps individual pages/routes
 * Prevents page errors from crashing the entire application
 */
class PageErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      hasError: false,
      error: null
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Page Error Boundary caught an error:', error, errorInfo);

    // Log to error tracking service
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
          boundaryType: 'page',
          page: window.location.pathname
        })
      }).catch(() => {});
    } catch (e) {
      // Silently fail
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null
    });
  };

  render() {
    if (this.state.hasError) {
      return (
        <PageErrorFallback
          error={this.state.error}
          onReset={this.handleReset}
        />
      );
    }

    return this.props.children;
  }
}

export default PageErrorBoundary;

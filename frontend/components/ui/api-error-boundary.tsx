'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Button } from './button';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from './alert';

interface ApiErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ApiErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

/**
 * Enterprise Grade Error Boundary for Component-Level Failures
 * Prevents entire page crashes when a single widget fails.
 */
export class ApiErrorBoundary extends Component<ApiErrorBoundaryProps, ApiErrorBoundaryState> {
  constructor(props: ApiErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ApiErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // In production, log this to Sentry via the stub introduced in global-error
    console.error("Uncaught component error:", error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
    // Useful if the error was transient network failure
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Alert variant="destructive" className="my-4">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Component Error</AlertTitle>
          <AlertDescription className="mt-2 flex flex-col gap-2">
            <p>This section of the interface encountered an error.</p>
            <div className="text-xs font-mono opacity-80">{this.state.error?.message}</div>
            <Button 
                variant="outline" 
                size="sm" 
                onClick={this.handleRetry} 
                className="w-fit mt-2 border-destructive/50 hover:bg-destructive/10"
            >
                <RefreshCw className="mr-2 h-3 w-3" /> Retry
            </Button>
          </AlertDescription>
        </Alert>
      );
    }

    return this.props.children;
  }
}

'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from './button';
import { Card, CardContent } from './card';
import { reportClientError } from '@/lib/telemetry/client-errors';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  moduleName?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ApiErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    reportClientError(error, {
      module: this.props.moduleName || 'Global',
      action: 'ApiErrorBoundary.componentDidCatch',
      metadata: {
        componentStack: errorInfo.componentStack,
      },
    });
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;

      return (
        <Card className="glass-card border-red-500/20 bg-red-500/5 animate-in fade-in zoom-in duration-300">
          <CardContent className="flex flex-col items-center justify-center py-8 text-center space-y-4">
            <div className="w-12 h-12 bg-red-500/10 rounded-2xl flex items-center justify-center border border-red-500/20">
              <AlertCircle className="h-6 w-6 text-red-500" />
            </div>
            <div className="space-y-1">
              <h3 className="font-bold text-white tracking-tight">Signal Disruption</h3>
              <p className="text-xs text-muted-foreground max-w-[200px] mx-auto">
                Failed to retrieve data for <span className="text-red-400 font-mono">{this.props.moduleName || 'this module'}</span>.
              </p>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => this.setState({ hasError: false, error: null })}
              className="h-8 rounded-lg border-white/10 hover:bg-white/5 transition-all gap-2"
            >
              <RefreshCw className="h-3 w-3" /> Re-sync
            </Button>
          </CardContent>
        </Card>
      );
    }

    return this.props.children;
  }
}

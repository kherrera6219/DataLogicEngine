'use client';

import { useEffect } from 'react';
import { RefreshCw, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { reportClientError } from '@/lib/telemetry/client-errors';

interface RouteErrorFallbackProps {
  error: Error & { digest?: string };
  reset: () => void;
  moduleName: string;
}

export function RouteErrorFallback({ error, reset, moduleName }: RouteErrorFallbackProps) {
  useEffect(() => {
    reportClientError(error, {
      module: moduleName,
      action: 'route-error',
    });
  }, [error, moduleName]);

  return (
    <div className="min-h-[40vh] flex items-center justify-center p-6">
      <div className="w-full max-w-lg rounded-2xl border border-red-500/20 bg-red-500/5 p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-red-500/15 border border-red-500/30 flex items-center justify-center">
            <AlertTriangle className="h-5 w-5 text-red-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-foreground">Module Error</h2>
            <p className="text-sm text-muted-foreground">Component: {moduleName}</p>
          </div>
        </div>
        <p className="text-sm text-muted-foreground">
          The module failed to render. Retry to recover this route segment.
        </p>
        <pre className="text-xs rounded-lg bg-black/20 p-3 overflow-auto">{error.message}</pre>
        <Button onClick={reset} className="gap-2">
          <RefreshCw className="h-4 w-4" />
          Retry Module
        </Button>
      </div>
    </div>
  );
}

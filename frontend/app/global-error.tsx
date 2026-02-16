'use client';

import { useEffect } from 'react';
import { reportClientError } from '@/lib/telemetry/client-errors';

const captureError = (error: Error) => {
    reportClientError(error, {
      module: 'global-error',
      action: 'render',
    });
};

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    captureError(error);
  }, [error]);

  const handleRecovery = () => {
      // Clear potentially corrupt local state
      try {
          localStorage.removeItem('user-session'); // Example cleanup
      } catch { /* ignore */ }
      
      // Attempt generic reset provided by Next.js
      reset();
      
      // Fallback: Hard reload if reset fails or loops
      setTimeout(() => {
          window.location.href = '/dashboard';
      }, 500);
  };

  return (
    <html lang="en">
      <body>
        <div className="flex min-h-screen flex-col items-center justify-center bg-background p-6 text-center">
          <div className="space-y-4 max-w-md">
            <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl text-destructive">
              System Error
            </h1>
            <h2 className="text-xl font-semibold tracking-tight">
                Something went wrong.
            </h2>
            <p className="text-muted-foreground text-sm">
              We&apos;ve logged this issue and our team has been notified.
              Please try refreshing the page.
            </p>
            
            <div className="bg-muted p-4 rounded-lg text-left font-mono text-xs overflow-auto max-h-32 my-4 border border-border">
               <div className="font-bold text-red-500 mb-1">Error Details:</div>
               {error.message || 'Unknown Error'}
               {error.digest && <div className="mt-1 text-muted-foreground">ID: {error.digest}</div>}
            </div>

            <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
                <button
                    onClick={handleRecovery}
                    className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-4 py-2"
                >
                    Reload Application
                </button>
                <button
                    onClick={() => window.location.href = '/'}
                    className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-10 px-4 py-2"
                >
                    Return Home
                </button>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}

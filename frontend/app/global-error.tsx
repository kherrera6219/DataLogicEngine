'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log the error to an error reporting service
    console.error(error);
  }, [error]);

  return (
    <html>
      <body>
        <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4 text-center">
          <h1 className="text-4xl font-bold bg-gradient-to-r from-red-600 to-rose-600 bg-clip-text text-transparent mb-4">
            Critical System Error
          </h1>
          <p className="text-muted-foreground max-w-md mb-8">
            An unexpected error has occurred in the Universal Knowledge Graph interface. 
            The system has prevented a total crash.
          </p>
          <div className="bg-card border p-4 rounded-md mb-6 w-full max-w-lg text-left overflow-auto max-h-48 text-xs font-mono text-destructive">
             {error.message || 'Unknown Error'}
             {error.digest && <div className="mt-2 text-muted-foreground opacity-70">Digest: {error.digest}</div>}
          </div>
          <button
            onClick={() => reset()}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
          >
            Attempt Recovery
          </button>
        </div>
      </body>
    </html>
  );
}

'use client';

import { RouteErrorFallback } from '@/components/ui/route-error-fallback';

export default function RunsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <RouteErrorFallback error={error} reset={reset} moduleName="Runs" />;
}

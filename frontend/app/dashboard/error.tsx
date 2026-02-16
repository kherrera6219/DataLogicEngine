'use client';

import { RouteErrorFallback } from '@/components/ui/route-error-fallback';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <RouteErrorFallback error={error} reset={reset} moduleName="Dashboard" />;
}

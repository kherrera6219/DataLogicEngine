'use client';

import { RouteErrorFallback } from '@/components/ui/route-error-fallback';

export default function AlgorithmsError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <RouteErrorFallback error={error} reset={reset} moduleName="Algorithm Registry" />;
}

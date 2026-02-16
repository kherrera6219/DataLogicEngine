'use client';

import { RouteErrorFallback } from '@/components/ui/route-error-fallback';

export default function McpError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return <RouteErrorFallback error={error} reset={reset} moduleName="MCP" />;
}

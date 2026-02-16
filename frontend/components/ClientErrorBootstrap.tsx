'use client';

import { useEffect } from 'react';
import { installGlobalClientErrorHandlers } from '@/lib/telemetry/client-errors';

export default function ClientErrorBootstrap() {
  useEffect(() => {
    return installGlobalClientErrorHandlers();
  }, []);

  return null;
}

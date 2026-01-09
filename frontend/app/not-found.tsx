'use client';

import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';

export default function NotFound() {
  const router = useRouter();

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col items-center justify-center gap-4">
      <div className="space-y-2 text-center">
        <h1 className="text-4xl font-bold tracking-tighter sm:text-6xl bg-gradient-to-r from-primary to-cyan-400 bg-clip-text text-transparent">
          404
        </h1>
        <h2 className="text-xl font-semibold tracking-tight">Page Not Found</h2>
        <p className="text-muted-foreground">
          The knowledge node you are looking for does not exist in this sector.
        </p>
      </div>
      <Button variant="outline" onClick={() => router.push('/dashboard')}>
        Return to Dashboard
      </Button>
    </div>
  );
}

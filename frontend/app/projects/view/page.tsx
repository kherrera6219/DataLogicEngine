'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { ProjectDetail } from '@/components/projects/ProjectDetail';

export default function ProjectDetailQueryPage() {
  const searchParams = useSearchParams();
  const id = searchParams.get('id')?.trim() || '';

  if (!id) {
    return (
      <div className="p-8 text-sm text-muted-foreground">
        Missing project ID. Return to <Link href="/projects" className="underline">Projects</Link>.
      </div>
    );
  }

  return <ProjectDetail id={id} />;
}

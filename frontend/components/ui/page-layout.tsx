'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { Breadcrumbs } from './breadcrumbs';

interface PageLayoutProps {
  children: React.ReactNode;
  title?: string;
  description?: string;
  breadcrumbs?: { label: string; href?: string }[];
  actions?: React.ReactNode;
  className?: string;
  containerClassName?: string;
}

export function PageLayout({
  children,
  title,
  description,
  breadcrumbs,
  actions,
  className,
  containerClassName,
}: PageLayoutProps) {
  return (
    <main className={cn("min-h-full bg-background text-foreground font-sans", className)}>
      <div className="min-h-full bg-[url('/grid-pattern.svg')] bg-[size:40px_40px] bg-fixed p-6 md:p-8">

      <div className={cn("container mx-auto max-w-7xl space-y-8", containerClassName)}>
        {(breadcrumbs || title || actions) && (
          <header className="space-y-4">
            {breadcrumbs && <Breadcrumbs items={breadcrumbs} className="mb-2" />}
            
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
              {(title || description) && (
                <div className="space-y-1">
                  {title && (
                    <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 dark:text-white">
                      {title}
                    </h1>
                  )}
                  {description && (
                    <p className="text-gray-500 dark:text-gray-400 font-medium">
                      {description}
                    </p>
                  )}
                </div>
              )}
              
              {actions && (
                <div className="flex flex-wrap gap-3">
                  {actions}
                </div>
              )}
            </div>
          </header>
        )}

        <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
          {children}
        </div>
      </div>
      </div>
    </main>
  );
}

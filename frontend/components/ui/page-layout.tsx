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
    <main className={cn("min-h-screen bg-gray-50/50 dark:bg-gray-950 p-6 md:p-8 relative overflow-x-hidden", className)}>
      {/* Universal Background Gradient */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,_rgba(37,99,235,0.03),transparent_50%)] pointer-events-none" />
      
      <div className={cn("container mx-auto max-w-7xl relative z-10 space-y-8", containerClassName)}>
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
    </main>
  );
}

'use client';

import Link from 'next/link';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BreadcrumbItem {
  label: string;
  href?: string;
}

interface BreadcrumbsProps {
  items: BreadcrumbItem[];
  className?: string;
}

export function Breadcrumbs({ items, className }: BreadcrumbsProps) {
  return (
    <nav 
      aria-label="Breadcrumb" 
      className={cn("flex items-center text-xs font-medium text-gray-500", className)}
    >
      <ol className="flex items-center gap-2">
        <li>
          <Link 
            href="/dashboard" 
            className="hover:text-white transition-colors flex items-center gap-1"
            aria-label="Back to Dashboard"
          >
            <Home className="h-3.5 w-3.5" />
          </Link>
        </li>
        
        {items.map((item, index) => (
          <li key={index} className="flex items-center gap-2">
            <ChevronRight className="h-3 w-3 opacity-30" />
            {item.href ? (
              <Link 
                href={item.href}
                className="hover:text-white transition-colors"
                aria-current={index === items.length - 1 ? 'page' : undefined}
              >
                {item.label}
              </Link>
            ) : (
              <span 
                className="text-blue-500 font-bold"
                aria-current="page"
              >
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  );
}

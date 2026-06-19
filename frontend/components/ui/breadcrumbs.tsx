import React from 'react';
import Link from 'next/link';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

/** Item in the breadcrumb navigation. */
interface BreadcrumbItem {
  /** The displayed text for the breadcrumb. */
  label: string;
  /** Optional href for linking. */
  href?: string;
  /** Optional aria-label for screen readers. */
  ariaLabel?: string;
}

/** Props for the Breadcrumbs component. */
interface BreadcrumbsProps extends React.HTMLAttributes<HTMLElement> {
  /** Array of breadcrumb items. */
  items: BreadcrumbItem[];
  /** Separator icon to display between items. */
  separator?: React.ReactNode;
  /** Whether to show the home icon. */
  showHome?: boolean;
  /** ARIA label for the navigation. */
  ariaLabel?: string;
}

export function Breadcrumbs({ 
  items, 
  className, 
  separator,
  showHome = true,
  ariaLabel = "Breadcrumb",
  ...props 
}: BreadcrumbsProps) {
  return (
    <nav
      aria-label={ariaLabel}
      className={cn("flex items-center text-xs font-medium text-gray-500", className)}
      {...props}
    >
      <ol className="flex items-center gap-2">
        {showHome && (
          <li>
            <Link
              href="/dashboard"
              className="hover:text-white transition-colors flex items-center gap-1"
              aria-label="Back to Dashboard"
            >
              <Home className="h-3.5 w-3.5" />
            </Link>
          </li>
        )}

        {items.map((item, index) => (
          <li key={index} className="flex items-center gap-2">
            {(index > 0 || showHome) && (separator || <ChevronRight className="h-3 w-3 opacity-30" />)}
            {item.href ? (
              <Link
                href={item.href}
                className="hover:text-white transition-colors"
                aria-label={item.ariaLabel}
                aria-current={index === items.length - 1 ? 'page' : undefined}
              >
                {item.label}
              </Link>
            ) : (
              <span
                className="text-blue-500 font-bold"
                aria-label={item.ariaLabel}
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

export type { BreadcrumbItem, BreadcrumbsProps }

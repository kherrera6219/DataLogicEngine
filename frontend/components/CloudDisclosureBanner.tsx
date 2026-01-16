
'use client';

import { useState, useEffect } from 'react';
import { X, Cloud, Info } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export function CloudDisclosureBanner() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Check if user has already dismissed the banner
    const dismissed = localStorage.getItem('cloud_disclosure_dismissed');
    if (!dismissed) {
      setIsVisible(true);
    }
  }, []);

  const dismiss = () => {
    setIsVisible(false);
    localStorage.setItem('cloud_disclosure_dismissed', 'true');
  };

  if (!isVisible) return null;

  return (
    <div className="relative isolate flex items-center gap-x-6 overflow-hidden bg-background px-6 py-2.5 sm:px-3.5 sm:before:flex-1 border-b border-blue-500/20 bg-blue-500/5">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <p className="text-sm leading-6 text-foreground">
          <strong className="font-semibold inline-flex items-center gap-2">
            <Cloud className="h-4 w-4 text-blue-500" />
            Cloud-Based Application
          </strong>
          <svg viewBox="0 0 2 2" className="mx-2 inline h-0.5 w-0.5 fill-current" aria-hidden="true">
            <circle cx={1} cy={1} r={1} />
          </svg>
          This application requires internet access and processes data using cloud AI services (OpenAI, Azure, Anthropic).
        </p>
        <Link
          href="/about/cloud-services"
          className="flex-none rounded-full bg-blue-600/10 px-3.5 py-1 text-sm font-semibold text-blue-500 shadow-sm hover:bg-blue-600/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-900"
        >
          Learn more <span aria-hidden="true">&rarr;</span>
        </Link>
      </div>
      <div className="flex flex-1 justify-end">
        <button type="button" className="-m-3 p-3 focus-visible:outline-offset-[-4px]" onClick={dismiss}>
          <span className="sr-only">Dismiss</span>
          <X className="h-5 w-5 text-gray-500 hover:text-foreground" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}

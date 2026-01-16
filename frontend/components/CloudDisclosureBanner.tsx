'use client';

import React, { useState, useEffect } from 'react';
import { Cloud, X, ExternalLink, ShieldCheck } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export function CloudDisclosureBanner() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // Standard mount check for client-side localStorage
    const isDismissed = localStorage.getItem('ukg_cloud_disclosure_dismissed');
    if (!isDismissed) {
      setIsVisible(true);
    }
  }, []);


  const handleDismiss = () => {
    localStorage.setItem('ukg_cloud_disclosure_dismissed', 'true');
    setIsVisible(false);
  };

  if (!isVisible) return null;

  return (
    <div className="bg-blue-600 text-white py-3 px-4 relative z-[100] animate-in slide-in-from-top duration-500">
      <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="bg-white/20 p-2 rounded-lg backdrop-blur-sm">
            <Cloud className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-bold flex items-center gap-2">
              Cloud-Hybrid Architecture Active
              <ShieldCheck className="h-3 w-3" />
            </p>
            <p className="text-xs text-blue-100 font-medium leading-tight">
              DataLogicEngine stores data locally but processes intelligence via cloud providers (OpenAI, Anthropic, Google).
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Button 
            variant="ghost" 
            size="sm" 
            asChild
            className="text-white hover:bg-white/20 transition-colors border border-white/20 h-8 text-[11px] font-bold"
          >
            <Link href="/about/cloud-services" className="inline-flex items-center gap-1">
              LEARN MORE <ExternalLink className="h-3 w-3" />
            </Link>
          </Button>
          
          <button 
            onClick={handleDismiss}
            className="p-1 hover:bg-white/20 rounded-md transition-all outline-none focus-visible:ring-2 focus-visible:ring-white"
            aria-label="Dismiss cloud disclosure"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
}

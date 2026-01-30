'use client';

import React from 'react';
import { useAuth } from "@/contexts/AuthContext";
import { Loader2 } from "lucide-react";

export function AppInitializer({ children }: { children: React.ReactNode }) {
  const { isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-[#0a0a0a] text-white">
        <div className="flex flex-col items-center space-y-4 animate-in fade-in duration-500">
          <Loader2 className="h-10 w-10 animate-spin text-blue-500" />
          <p className="text-sm font-medium tracking-widest uppercase text-gray-400">
            Initializing DataLogicEngine...
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

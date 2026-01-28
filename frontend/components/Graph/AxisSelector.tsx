'use client';

import { useRef } from 'react';
import { cn } from '@/lib/utils';

export const AXIS_NAMES = [
  "Pillars", "Sectors", "Honeycomb", "Branches", "Nodes", 
  "Octopus", "Spiderweb", "Roles", "Quals", "Regulatory", 
  "Compliance", "Location", "Temporal", "Risk", "Federated", 
  "Arrows", "Analytics"
];

interface AxisSelectorProps {
  activeAxis: number;
  onChange: (axis: number) => void;
}

export function AxisSelector({ activeAxis, onChange }: AxisSelectorProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  return (
    <div className="w-full bg-white/5 dark:bg-black/20 backdrop-blur-md border-b border-white/10 overflow-hidden">
      <div 
        ref={scrollRef}
        className="flex items-center gap-1 p-2 overflow-x-auto no-scrollbar scroll-smooth"
        role="tablist"
        aria-label="17-Axis Selection"
      >
        {AXIS_NAMES.map((name, index) => {
          const axisNum = index + 1;
          const isActive = activeAxis === axisNum;
          
          return (
            <button
              key={name}
              onClick={() => onChange(axisNum)}
              role="tab"
              aria-selected={isActive}
              aria-controls="graph-viewport"
              className={cn(
                "relative flex-shrink-0 px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-300 outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 ring-offset-black",
                isActive 
                  ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20" 
                  : "text-muted-foreground hover:bg-white/10 hover:text-foreground"
              )}
            >
              <div className="flex flex-col items-center">
                <span className="opacity-50 text-[9px] mb-0.5">Axis {axisNum}</span>
                <span>{name}</span>
              </div>
              {isActive && (
                <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-1 h-1 bg-white rounded-full" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}

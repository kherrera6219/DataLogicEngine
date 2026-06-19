'use client';

import React from 'react';
import { Search, Settings, LayoutGrid, Download, HelpCircle } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Breadcrumbs } from "@/components/ui/breadcrumbs";
import { usePathname, useRouter } from "next/navigation";

export function CommandBar() {
  const pathname = usePathname();
  const router = useRouter();
  const [query, setQuery] = React.useState('');
  const searchInputRef = React.useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    const handleGlobalShortcut = (event: KeyboardEvent) => {
      if (event.altKey && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        searchInputRef.current?.focus();
        searchInputRef.current?.select();
      }
    };

    window.addEventListener('keydown', handleGlobalShortcut);
    return () => {
      window.removeEventListener('keydown', handleGlobalShortcut);
    };
  }, []);
  
  const getBreadcrumbs = () => {
    if (pathname === '/dashboard') return [{ label: "Executive Dashboard" }];
    if (pathname === '/graph') return [{ label: "Knowledge Graph Explorer" }];
    if (pathname === '/chat') return [{ label: "Intelligence Interface" }];
    return [];
  };

  return (
    <div 
      className="w-full h-14 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-4 z-50 shrink-0"
      role="toolbar"
      aria-label="Primary Application Toolbar"
    >
      <div className="flex items-center gap-4">
        <button
          type="button"
          className="p-2 hover:bg-gray-800 rounded-lg cursor-pointer"
          aria-label="Open application launcher"
          onClick={() => router.push('/dashboard')}
        >
          <LayoutGrid className="h-5 w-5 text-gray-400" aria-hidden="true" />
        </button>
        <div className="h-6 w-px bg-gray-800" aria-hidden="true" />
        <div className="flex flex-col">
          <h2 className="text-[10px] font-bold text-white tracking-widest uppercase opacity-70">
            DataLogic <span className="text-blue-500">Engine</span>
          </h2>
          <Breadcrumbs items={getBreadcrumbs()} />
        </div>
        <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 text-[10px] px-1.5 font-bold ml-2">
           PROD
        </Badge>
      </div>

      <div className="flex-1 max-w-md mx-8 hidden md:block">
        <form
          className="relative group"
          onSubmit={(event) => {
            event.preventDefault();
            const trimmed = query.trim();
            router.push(trimmed ? `/graph?search=${encodeURIComponent(trimmed)}` : '/graph');
          }}
        >
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500 group-focus-within:text-blue-500" />
          <Input 
            ref={searchInputRef}
            className="w-full bg-gray-800/50 border-gray-700/50 h-9 pl-10 focus-visible:ring-blue-500 transition-all rounded-xl" 
            placeholder="Search nodes, pillars, or compliance controls..." 
            aria-label="Global search for nodes and compliance controls"
            aria-keyshortcuts="Alt+K"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </form>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-9 w-9 text-gray-400 hover:text-white hover:bg-gray-800 rounded-xl"
            aria-label="Help and Documentation"
            onClick={() => router.push('/about')}
          >
            <HelpCircle className="h-5 w-5" aria-hidden="true" />
          </Button>
          {[
            { Icon: Download, label: "Open export history", href: "/tools/history" },
            { Icon: Settings, label: "Account and System Settings", href: "/settings" }
          ].map(({ Icon, label, href }, idx) => (
             <Button key={idx} variant="ghost" size="icon" className="h-9 w-9 text-gray-400 hover:text-white hover:bg-gray-800 rounded-xl" aria-label={label} onClick={() => router.push(href)}>
               <Icon className="h-5 w-5" aria-hidden="true" />
             </Button>
          ))}
          <button
            type="button"
            className="h-9 w-9 rounded-xl bg-blue-600 flex items-center justify-center text-white text-xs font-bold cursor-pointer"
            aria-label="User Profile: Admin User"
            onClick={() => router.push('/profile')}
          >
             AD
          </button>
        </div>
      </div>
    </div>
  );
}

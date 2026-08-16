'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard, MessageSquare, Database, Folder, FlaskConical,
  BookOpen, Share2, Binary, ScrollText, ShieldCheck, BarChart3,
  ClipboardCheck, Settings, Hexagon, PanelLeftClose, PanelLeftOpen, Activity
} from 'lucide-react';
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { getLocalStorageItem, setLocalStorageItem } from '@/lib/state/storage';

interface SidebarItemProps {
  icon: React.ElementType;
  label: string;
  href: string;
  isActive: boolean;
  isCollapsed?: boolean;
}

function SidebarItem({ icon: Icon, label, href, isActive, isCollapsed }: SidebarItemProps) {
  return (
    <Link 
      href={href} 
      className={cn("w-full block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded-lg", isCollapsed ? "flex justify-center" : "")}
      aria-current={isActive ? "page" : undefined}
      title={isCollapsed ? label : undefined}
    >
      <div className={cn(
        "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group relative reveal-hover",
        isActive 
          ? "bg-white/5 text-blue-400 shadow-[0_4px_12px_rgba(0,0,0,0.1)] border border-white/5" 
          : "text-gray-400 hover:text-gray-200 hover:bg-white/5",
        isCollapsed && "justify-center px-0 w-10 h-10"
      )}>
        <Icon className={cn("h-5 w-5 shrink-0 transition-all duration-300", isActive ? "text-blue-400 drop-shadow-[0_0_8px_rgba(59,130,246,0.5)]" : "text-gray-500 group-hover:text-gray-300")} aria-hidden="true" />
        
        {!isCollapsed && (
          <span className={cn("text-base-fluent transition-colors", isActive ? "text-blue-100 font-semibold" : "")}>
            {label}
          </span>
        )}
        
        {isActive && !isCollapsed && (
             <div className="absolute left-0 w-1 h-5 rounded-r-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.8)]" aria-hidden="true"></div>
        )}
      </div>
    </Link>
  );
}

function SectionLabel({ label, isCollapsed }: { label: string; isCollapsed?: boolean }) {
  return (
    <div className={cn(
      "text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-2 px-3 transition-opacity duration-300",
      isCollapsed && "text-center opacity-0 h-0 overflow-hidden"
    )}>
      {label}
    </div>
  );
}

export function AppSidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  
  const [isCollapsed, setIsCollapsed] = React.useState(() => {
    if (typeof window !== 'undefined') {
      const stored = getLocalStorageItem('ukg.sidebar.collapsed');
      if (stored === 'true' || stored === 'false') {
        return stored === 'true';
      }
    }
    return false;
  });

  const toggleSidebar = React.useCallback(() => {
    setIsCollapsed((prev) => {
      const next = !prev;
      if (typeof window !== 'undefined') {
        setLocalStorageItem('ukg.sidebar.collapsed', String(next));
      }
      return next;
    });
  }, []);

  const isAdmin = Boolean(user?.is_admin || user?.role === 'admin' || user?.role === 'owner');
  const initials = user?.username
    ? user.username
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase())
        .join('')
    : 'U';
  const roleLabel = user?.role || (user?.is_admin ? 'admin' : 'user');

  // Helper to determine active state
  const isActive = (path: string) => {
      if (path === '/dashboard' && pathname === '/dashboard') return true;
      if (path !== '/dashboard' && pathname?.startsWith(path)) return true;
      return false;
  };

  // Hide on auth pages
  if (pathname === '/login' || pathname === '/register') return null;

  return (
    <aside
      data-testid="app-sidebar"
      className={cn(
      "h-screen bg-[#111827] border-r border-slate-700/70 flex flex-col transition-all duration-300 z-50 shadow-2xl shrink-0",
      isCollapsed ? "w-20" : "w-64"
    )}
      aria-label="Main application navigation"
    >
      
      {/* Brand Header */}
      <div className="h-16 flex items-center justify-between px-4 border-b border-white/5" role="banner">
        <div className="flex items-center gap-3 group">
           <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shrink-0 shadow-lg shadow-blue-900/20 group-hover:scale-105 transition-transform">
              <Hexagon className="h-5 w-5 text-white fill-white/20" aria-hidden="true" />
           </div>
           {!isCollapsed && (
              <div className="animate-in fade-in slide-in-from-left-2 duration-300">
                 <h2 className="font-bold text-sm tracking-wide text-white">UKG<span className="text-gray-300 mx-1">/</span>REGISTRY</h2>
                 <div className="text-[10px] text-gray-300 font-mono tracking-wider">ENTERPRISE v2.4</div>
              </div>
           )}
        </div>
        <Button
          data-testid="app-sidebar-toggle"
          variant="ghost"
          size="icon"
          className="h-8 w-8 text-gray-400 hover:text-white hover:bg-white/10 focus-visible:ring-2 focus-visible:ring-blue-500"
          onClick={toggleSidebar}
          aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-controls="sidebar-nav"
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? <PanelLeftOpen className="h-4 w-4" aria-hidden="true" /> : <PanelLeftClose className="h-4 w-4" aria-hidden="true" />}
        </Button>
      </div>

      {/* Navigation */}
      <nav 
        id="sidebar-nav"
        className="flex-1 py-6 px-3 space-y-1 overflow-y-auto custom-scrollbar"
        role="navigation"
        aria-label="Application sections"
      >
         <SectionLabel label="Workspace" isCollapsed={isCollapsed} />
         <SidebarItem icon={LayoutDashboard} label="Dashboard" href="/dashboard" isActive={isActive('/dashboard')} isCollapsed={isCollapsed} />
         <SidebarItem icon={MessageSquare} label="Governed Chat" href="/chat" isActive={isActive('/chat')} isCollapsed={isCollapsed} />
         <SidebarItem icon={Folder} label="Sessions" href="/projects" isActive={isActive('/projects')} isCollapsed={isCollapsed} />
         <SidebarItem icon={FlaskConical} label="Simulations" href="/simulations" isActive={isActive('/simulations')} isCollapsed={isCollapsed} />
         <SidebarItem icon={Database} label="MCP Hub" href="/mcp" isActive={isActive('/mcp')} isCollapsed={isCollapsed} />

         <div className="my-4 border-t border-white/5 mx-2" role="separator" aria-hidden="true"></div>
         <SectionLabel label="Knowledge" isCollapsed={isCollapsed} />
         <SidebarItem icon={BookOpen} label="Knowledge Base" href="/knowledge" isActive={isActive('/knowledge')} isCollapsed={isCollapsed} />
         <SidebarItem icon={Share2} label="Knowledge Graph" href="/graph" isActive={isActive('/graph')} isCollapsed={isCollapsed} />

         <div className="my-4 border-t border-white/5 mx-2" role="separator" aria-hidden="true"></div>
         <SectionLabel label="Trace & Review" isCollapsed={isCollapsed} />
         <SidebarItem icon={ScrollText} label="Trace Explorer" href="/runs" isActive={isActive('/runs')} isCollapsed={isCollapsed} />
         <SidebarItem icon={ShieldCheck} label="Truth Engine" href="/truth-engine" isActive={isActive('/truth-engine')} isCollapsed={isCollapsed} />
         <SidebarItem icon={BarChart3} label="Analytics" href="/analytics" isActive={isActive('/analytics')} isCollapsed={isCollapsed} />

         <div className="my-4 border-t border-white/5 mx-2" role="separator" aria-hidden="true"></div>
         <SectionLabel label="System" isCollapsed={isCollapsed} />
         {isAdmin && (
           <>
             <SidebarItem icon={Binary} label="Algorithms" href="/algorithms" isActive={isActive('/algorithms')} isCollapsed={isCollapsed} />
             <SidebarItem icon={Activity} label="Diagnostics" href="/admin/diagnostics" isActive={isActive('/admin/diagnostics')} isCollapsed={isCollapsed} />
             <SidebarItem icon={ClipboardCheck} label="Compliance" href="/admin/compliance" isActive={isActive('/admin/compliance')} isCollapsed={isCollapsed} />
           </>
         )}
         <SidebarItem icon={Settings} label="Settings" href="/settings" isActive={isActive('/settings')} isCollapsed={isCollapsed} />
     </nav>

     {/* User Footer */}
     <div className="p-4 border-t border-white/5 bg-black/20" role="contentinfo">
       <div className={cn("flex items-center gap-3", isCollapsed ? "justify-center" : "")} title={`${user?.username} - ${roleLabel}`}>
          <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-gray-700 to-gray-600 border border-white/10 flex items-center justify-center shrink-0 ring-2 ring-transparent group-hover:ring-blue-500/50 transition-all" aria-label={`User avatar: ${user?.username}`}>
             <span className="text-xs font-bold text-white">{initials}</span>
          </div>
           
          {!isCollapsed && (
             <div className="flex-1 min-w-0 animate-in fade-in slide-in-from-left-2 duration-300">
                <div className="text-sm font-medium text-white truncate">{user?.username || 'User'}</div>
                <div className="text-xs text-blue-200 truncate">{roleLabel}</div>
             </div>
          )}
           
       </div>
     </div>
   </aside>
  );
}

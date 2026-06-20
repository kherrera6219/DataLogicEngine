'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext'; // Added useAuth import
import { Menu, X, Hexagon, User as UserIcon, Settings } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ThemeToggle } from '@/components/ThemeToggle';
import { CloudStatusIndicator } from '@/components/ui/cloud-status-indicator';
import { // Added DropdownMenu imports
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export function NavBar() {
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const { user, isAuthenticated } = useAuth();
  const mobileMenuRef = useRef<HTMLDivElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  // Handle keyboard navigation (Escape to close menu)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMenuOpen) {
        setIsMenuOpen(false);
        menuButtonRef.current?.focus();
      }
    };

    if (isMenuOpen) {
      document.addEventListener('keydown', handleKeyDown);
      return () => document.removeEventListener('keydown', handleKeyDown);
    }
  }, [isMenuOpen]);

  // Hide NavBar on login/register pages
  if (pathname === '/login' || pathname === '/register') return null;

  // Primary page navigation lives in AppSidebar (single authoritative nav).
  // NavBar is global chrome only: logo, cloud status, theme, and the account menu.
  return (
    <header 
      className="bg-background/80 backdrop-blur-xl supports-[backdrop-filter]:bg-background/60 border-b border-white/5 sticky top-0 z-50 shadow-sm shadow-black/5"
      role="banner"
      aria-label="Main navigation bar"
    >
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          
          {/* Logo */}
          <Link 
            href="/" 
            className="flex items-center gap-2 font-bold text-lg text-foreground hover:opacity-80 transition-opacity focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 rounded"
            aria-label="DataLogicEngine Home"
          >
            <Hexagon className="h-6 w-6 text-primary fill-primary/20" />
            <span className="tracking-tight">DataLogicEngine</span>
          </Link>

          {/* User Menu / Auth */}
          <div className="hidden md:flex items-center gap-2">
             <CloudStatusIndicator className="mr-2" />
             <ThemeToggle />
             {isAuthenticated && user ? (
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button 
                          variant="ghost" 
                          className="relative h-8 w-8 rounded-full focus-visible:ring-2 focus-visible:ring-blue-500" 
                          aria-label="User Menu"
                          aria-haspopup="true"
                        >
                            <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center border border-border">
                                <UserIcon className="h-4 w-4" />
                            </div>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="w-56" align="end" forceMount role="menu">
                        <DropdownMenuLabel className="font-normal">
                            <div className="flex flex-col space-y-1">
                                <div className="flex items-center justify-between">
                                    <p className="text-sm font-medium leading-none">{user.username}</p>
                                    {user.role && (
                                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-primary/10 text-primary border border-primary/20 uppercase tracking-wider font-bold">
                                            {user.role}
                                        </span>
                                    )}
                                </div>
                                <p className="text-xs leading-none text-muted-foreground truncate">
                                    {user.windows_sid ? `Windows Identity: ${user.username}` : user.email}
                                </p>
                            </div>
                        </DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem asChild role="menuitem">
                            <Link href="/settings"><Settings className="mr-2 h-4 w-4"/> Settings</Link>
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
             ) : (
                null
             )}
          </div>
           
           {/* Mobile Menu Button */}
           <button 
             ref={menuButtonRef}
             className="md:hidden p-2 rounded-xl hover:bg-muted text-muted-foreground transition-all outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
             onClick={() => setIsMenuOpen(!isMenuOpen)}
             aria-label={isMenuOpen ? "Close main menu" : "Open main menu"}
             aria-expanded={isMenuOpen}
             aria-controls="mobile-nav-drawer"
           >
             {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
           </button>
        </div>
      </div>
       
       {/* Mobile Nav Drawer */}
       {isMenuOpen && (
         <nav 
           ref={mobileMenuRef}
           id="mobile-nav-drawer"
           className="md:hidden border-t border-white/5 bg-background/95 backdrop-blur-2xl animate-in slide-in-from-top duration-300"
           role="navigation"
           aria-label="Mobile account menu"
         >
           <div className="flex flex-col p-4 space-y-1">
            <div>
                {isAuthenticated && user ? (
                    <div className="space-y-3">
                        <div className="flex items-center gap-3 px-4 py-2">
                            <UserIcon className="h-5 w-5 text-muted-foreground" aria-hidden="true" />
                            <div className="flex flex-col">
                                <span className="text-sm font-medium">{user.username}</span>
                                <span className="text-xs text-muted-foreground">{user.email}</span>
                            </div>
                        </div>
                    </div>
                ) : (
                    null
                )}
            </div>
          </div>
        </nav>
      )}
    </header>
  );
}

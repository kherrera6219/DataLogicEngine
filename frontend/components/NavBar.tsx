'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext'; // Added useAuth import
import { Menu, X, Hexagon, User as UserIcon, LogOut, Settings } from 'lucide-react'; // Modified lucide-react imports
import { Button } from '@/components/ui/button';
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
  const { user, logout, isLoading } = useAuth(); // Replaced hardcoded auth state with useAuth

  // Hide NavBar on login/register pages
  if (pathname === '/login' || pathname === '/register') return null;

  // TODO: Real authentication state via Context
  // const isAuthenticated = true; // Removed
  // const username = "Admin User"; // Removed
  // const userInitials = "AU"; // Removed

  const navItems = [
    { name: 'Simulations', href: '/simulations', authRequired: true },
    { name: 'About', href: '/about' },
  ];

  return (
    <header className="bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b border-border sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          
          {/* Logo */}
          <Link 
            href="/" 
            className="flex items-center gap-2 font-bold text-lg text-foreground hover:opacity-80 transition-opacity"
            aria-label="DataLogicEngine Home"
          >
            <Hexagon className="h-6 w-6 text-primary fill-primary/20" />
            <span className="tracking-tight">DataLogicEngine</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => (
              !item.authRequired || isAuthenticated ? (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "px-3 py-2 rounded-md text-sm font-medium transition-colors hover:bg-muted hover:text-foreground",
                    pathname === item.href
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground"
                  )}
                >
                  {item.name}
                </Link>
              ) : null
            ))}
          </nav>

          {/* User Menu / Auth */}
            ) : (
              <div className="flex gap-2">
                <Link href="/login">
                  <Button variant="ghost" size="sm">Log in</Button>
                </Link>
                <Link href="/register">
                  <Button size="sm">Sign up</Button>
                </Link>
              </div>
            )}
          </div>
          
           {/* Mobile Menu Button */}
           <button 
             className="md:hidden p-2 rounded-md hover:bg-muted text-muted-foreground"
             onClick={() => setIsMenuOpen(!isMenuOpen)}
             aria-label="Toggle menu"
           >
             {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
           </button>
        </div>
      </div>
      
      {/* Mobile Nav Drawer */}
      {isMenuOpen && (
        <div className="md:hidden border-t border-border bg-background">
          <nav className="flex flex-col p-4 space-y-1">
             {navItems.map((item) => (
              !item.authRequired || isAuthenticated ? (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMenuOpen(false)}
                  className={cn(
                    "px-4 py-3 rounded-md text-sm font-medium transition-colors",
                    pathname === item.href
                      ? "bg-accent text-accent-foreground"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  {item.name}
                </Link>
              ) : null
            ))}
            <div className="pt-4 mt-4 border-t border-border">
                {isAuthenticated ? (
                    <div className="flex items-center gap-3 px-4 py-2">
                        <User className="h-5 w-5 text-muted-foreground" />
                        <span className="text-sm font-medium">{username}</span>
                    </div>
                ) : (
                    <div className="grid gap-2">
                        <Button variant="outline" className="w-full">Log in</Button>
                        <Button className="w-full">Sign up</Button>
                    </div>
                )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}

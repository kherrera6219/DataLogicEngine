'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext'; // Added useAuth import
import { Menu, X, Hexagon, User as UserIcon, LogOut, Settings } from 'lucide-react';
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
  const { user, logout, isAuthenticated } = useAuth();

  // Hide NavBar on login/register pages
  if (pathname === '/login' || pathname === '/register') return null;

  const navItems = [
    { name: 'Dashboard', href: '/dashboard', authRequired: true },
    { name: 'Simulations', href: '/simulations', authRequired: true },
    { name: 'Knowledge', href: '/knowledge', authRequired: true },
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
          <div className="hidden md:flex items-center gap-4">
             {isAuthenticated && user ? (
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="relative h-8 w-8 rounded-full" aria-label="User Menu">
                            <div className="h-8 w-8 rounded-full bg-secondary flex items-center justify-center border border-border">
                                <UserIcon className="h-4 w-4" />
                            </div>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent className="w-56" align="end" forceMount>
                        <DropdownMenuLabel className="font-normal">
                            <div className="flex flex-col space-y-1">
                                <p className="text-sm font-medium leading-none">{user.username}</p>
                                <p className="text-xs leading-none text-muted-foreground">{user.email}</p>
                            </div>
                        </DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem asChild>
                            <Link href="/settings"><Settings className="mr-2 h-4 w-4"/> Settings</Link>
                        </DropdownMenuItem>
                         {user.is_admin && (
                            <DropdownMenuItem asChild>
                                <Link href="/admin"><Hexagon className="mr-2 h-4 w-4"/> Admin</Link>
                            </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={() => logout()} className="text-destructive focus:text-destructive">
                            <LogOut className="mr-2 h-4 w-4" />
                            Log out
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
             ) : (
                <div className="space-x-2">
                    <Button variant="ghost" asChild><Link href="/login">Login</Link></Button>
                    <Button asChild><Link href="/register">Sign up</Link></Button>
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
                {isAuthenticated && user ? (
                    <div className="space-y-3">
                        <div className="flex items-center gap-3 px-4 py-2">
                            <UserIcon className="h-5 w-5 text-muted-foreground" />
                            <div className="flex flex-col">
                                <span className="text-sm font-medium">{user.username}</span>
                                <span className="text-xs text-muted-foreground">{user.email}</span>
                            </div>
                        </div>
                        <Button variant="outline" className="w-full justify-start" onClick={() => { logout(); setIsMenuOpen(false); }}>
                            <LogOut className="mr-2 h-4 w-4" /> Log out
                        </Button>
                    </div>
                ) : (
                    <div className="grid gap-2">
                        <Button variant="outline" className="w-full" asChild><Link href="/login">Log in</Link></Button>
                        <Button className="w-full" asChild><Link href="/register">Sign up</Link></Button>
                    </div>
                )}
            </div>
          </nav>
        </div>
      )}
    </header>
  );
}

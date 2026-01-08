'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { useState } from 'react';

export function NavBar() {
  const pathname = usePathname();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // TODO: Real authentication state
  const isAuthenticated = true; 
  const username = "Admin User"; 

  const navItems = [
    { name: 'Home', href: '/' },
    { name: 'Dashboard', href: '/dashboard', authRequired: true },
    { name: 'Chat', href: '/chat', authRequired: true },
    { name: 'Knowledge', href: '/knowledge', authRequired: true },
    { name: 'Graph', href: '/graph', authRequired: true },
    { name: 'Simulations', href: '/simulations', authRequired: true },
    { name: 'About', href: '/about' },
  ];

  return (
    <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 font-bold text-lg text-gray-900 dark:text-gray-100 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
            <span className="text-blue-600 dark:text-blue-400">◆</span>
            <span>DataLogicEngine</span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex gap-1">
            {navItems.map((item) => (
              !item.authRequired || isAuthenticated ? (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "px-3 py-2 rounded-md text-sm font-medium transition-colors",
                    pathname === item.href
                      ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-gray-800"
                  )}
                >
                  {item.name}
                </Link>
              ) : null
            ))}
          </nav>

          {/* User Menu */}
          <div className="hidden md:flex items-center gap-4">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                 <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{username}</span>
                 <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 flex items-center justify-center font-bold">
                    {username[0]}
                 </div>
              </div>
            ) : (
              <div className="flex gap-2">
                <Link href="/login" className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg">
                  Log in
                </Link>
                <Link href="/register" className="px-4 py-2 text-sm font-medium bg-blue-600 text-white hover:bg-blue-700 rounded-lg">
                  Sign up
                </Link>
              </div>
            )}
          </div>
          
           {/* Mobile Menu Button */}
           <button 
             className="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800"
             onClick={() => setIsMenuOpen(!isMenuOpen)}
           >
             <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
           </button>
        </div>
      </div>
      
      {/* Mobile Nav */}
      {isMenuOpen && (
        <div className="md:hidden border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900/50">
          <nav className="flex flex-col p-4 space-y-1">
             {navItems.map((item) => (
              !item.authRequired || isAuthenticated ? (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsMenuOpen(false)}
                  className={cn(
                    "px-4 py-3 rounded-lg text-sm font-medium transition-colors",
                    pathname === item.href
                      ? "bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-gray-800"
                  )}
                >
                  {item.name}
                </Link>
              ) : null
            ))}
          </nav>
        </div>
      )}
    </header>
  );
}

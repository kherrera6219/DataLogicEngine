import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { NavBar } from "@/components/NavBar";
import { AuthProvider } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { SWRConfig } from 'swr';

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DataLogicEngine UKG",
  description: "Universal Knowledge Graph Enterprise System",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "UKG",
  },
  formatDetection: {
    telephone: false,
  },
};

import { ToastProvider } from "@/components/ui/use-toast";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <a 
          href="#main-content" 
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-lg focus:font-bold focus:shadow-2xl"
        >
          Skip to main content
        </a>
        <ThemeProvider>
          <SWRConfig value={{
            revalidateOnFocus: false,
            revalidateOnReconnect: true,
            dedupingInterval: 3000,
            errorRetryCount: 3,
            shouldRetryOnError: true
          }}>
            <AuthProvider>
              <ToastProvider>
                <NavBar />
                <main id="main-content" className="outline-none" tabIndex={-1}>
                  {children}
                </main>
              </ToastProvider>
            </AuthProvider>
          </SWRConfig>
        </ThemeProvider>
      </body>
    </html>
  );
}

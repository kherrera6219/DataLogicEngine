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
import { CloudDisclosureBanner } from "@/components/CloudDisclosureBanner";
import DesktopStatus from "@/components/DesktopStatus";

import { AppSidebar } from "@/components/layout/AppSidebar";
import { useAuth } from "@/contexts/AuthContext";
import { Loader2 } from "lucide-react";

function AppInitializer({ children }: { children: React.ReactNode }) {
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
              <AppInitializer>
                <ToastProvider>
                  <div className="flex h-screen w-full bg-[#111111] overflow-hidden">
                    <AppSidebar />
                    <div className="flex-1 flex flex-col min-w-0">
                      <aside aria-label="Cloud Dependency">
                        <CloudDisclosureBanner />
                      </aside>
                      <NavBar />
                      <div id="main-content" className="flex-1 overflow-y-auto scroll-smooth outline-none" tabIndex={-1}>
                        {children}
                      </div>
                    </div>
                  </div>
                  <DesktopStatus />
                </ToastProvider>
              </AppInitializer>
            </AuthProvider>
          </SWRConfig>
        </ThemeProvider>
      </body>
    </html>
  );
}

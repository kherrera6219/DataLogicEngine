import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { NavBar } from "@/components/NavBar";
import { AuthProvider } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { FeatureFlagProvider } from "@/contexts/FeatureFlagContext";
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
import DesktopStatus from "@/components/DesktopStatus";

import { AppSidebar } from "@/components/layout/AppSidebar";

import { AppInitializer } from "@/components/AppInitializer";

import { ApiErrorBoundary } from "@/components/ui/api-error-boundary";
import { CloudDisclosureBanner } from "@/components/CloudDisclosureBanner";
import { FeatureFlagGate } from "@/components/feature-flags/FeatureFlagGate";
import ClientErrorBootstrap from "@/components/ClientErrorBootstrap";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <nav aria-label="Skip links">
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100] focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded-lg focus:font-bold focus:shadow-2xl"
          >
            Skip to main content
          </a>
        </nav>
        <FeatureFlagProvider>
          <ClientErrorBootstrap />
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
                    <ApiErrorBoundary moduleName="UKG Root">
                      <div className="flex h-screen w-full bg-background text-foreground overflow-hidden">
                        <AppSidebar />
                        <div className="flex-1 flex flex-col min-w-0">
                          <FeatureFlagGate flag="cloudDisclosureBanner">
                            <aside aria-label="Cloud Dependency">
                              <CloudDisclosureBanner />
                            </aside>
                          </FeatureFlagGate>
                          <NavBar />
                          <main id="main-content" className="flex-1 overflow-y-auto scroll-smooth outline-none" tabIndex={-1}>
                            <h1 className="sr-only">DataLogicEngine Workspace</h1>
                            {children}
                          </main>
                        </div>
                      </div>
                      <DesktopStatus />
                    </ApiErrorBoundary>
                  </ToastProvider>
                </AppInitializer>
              </AuthProvider>
            </SWRConfig>
          </ThemeProvider>
        </FeatureFlagProvider>
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { NavBar } from "@/components/NavBar";
import { AuthProvider } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/contexts/ThemeContext";

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
        <ThemeProvider>
          <AuthProvider>
            <ToastProvider>
              <NavBar />
              {children}
            </ToastProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}

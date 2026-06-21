"use client";

import {
  createContext,
  useContext,
  useEffect,
  useState,
  ReactNode,
  useCallback,
} from "react";
import { useRouter, usePathname } from "next/navigation";
import { api, User } from "@/lib/api";
import { shouldUseDesktopSessionFlow } from "@/lib/runtime/policy";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  showNotification: (
    message: string,
    type: "success" | "error" | "info" | "warning",
  ) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Notification event for cross-component communication
const NOTIFICATION_EVENT = "auth-notification";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  const showNotification = useCallback(
    (
      message: string,
      type: "success" | "error" | "info" | "warning" = "info",
    ) => {
      // Dispatch custom event that ToastProvider can listen to
      window.dispatchEvent(
        new CustomEvent(NOTIFICATION_EVENT, {
          detail: { message, type },
        }),
      );
    },
    [],
  );

  const checkAuth = useCallback(async () => {
    try {
      const data = await api.auth.check();
      if (data?.user) {
        setUser(data.user);
      } else {
        if (shouldUseDesktopSessionFlow()) {
          // Desktop "Zero-Config" experience is desktop-runtime only.
          const autoLoginResponse = await api.auth
            .desktopAutoLogin()
            .catch(() => null);
          if (autoLoginResponse && autoLoginResponse.user) {
            setUser(autoLoginResponse.user);
            return;
          }
        }
        setUser(null);
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = async () => {
    // Single-mode: authentication is at the OS level (Windows identity + signed
    // Electron loopback) — there is no app-level session to tear down and no web
    // login to return to. Return to the dashboard (the installed app's home).
    router.push("/dashboard");
    router.refresh();
  };

  useEffect(() => {
    let cancelled = false;
    async function init() {
      await checkAuth();
      if (cancelled) return;
    }
    void init();
    return () => { cancelled = true; };
  }, [checkAuth]);

  // Protected Route Logic + Desktop Auto-Redirect
  useEffect(() => {
    if (isLoading) return;
    const publicRoutes = ["/login", "/register", "/"];
    const isPublic = publicRoutes.some((p) => pathname?.startsWith(p));
    const desktopRuntime = shouldUseDesktopSessionFlow();

    if (!user && !isPublic && !desktopRuntime) {
      router.push("/login");
    }

    if (desktopRuntime && pathname === "/login") {
      router.push("/dashboard");
      return;
    }

    // Web sessions skip landing/login once authenticated.
    // Desktop keeps the landing page as the installed app's entry point.
    if (!desktopRuntime && user && (pathname === "/" || pathname === "/login")) {
      router.push("/dashboard");
    }
  }, [user, isLoading, pathname, router]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        logout,
        checkAuth,
        showNotification,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

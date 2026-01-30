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
import { LoginCredentials } from "@/lib/api/auth";

interface MFAState {
  required: boolean;
  sessionId?: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  mfaState: MFAState;
  login: (credentials: LoginCredentials) => Promise<void>;
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
  const [mfaState, setMfaState] = useState<MFAState>({ required: false });
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

  const checkAuth = async () => {
    try {
      const data = await api.auth.check();
      if (data?.user) {
        setUser(data.user);
      } else {
        // If not authenticated, try desktop auto-login if on Windows
        // This is a "Zero-Config" experience for desktop users
        const autoLoginResponse = await api.auth
          .desktopAutoLogin()
          .catch(() => null);
        if (autoLoginResponse && autoLoginResponse.user) {
          setUser(autoLoginResponse.user);
        } else {
          setUser(null);
        }
      }
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await api.auth.login(credentials);
      // If we're here, the request was successful (2xx)
      if (response && response.user) {
        setUser(response.user);
        router.push("/dashboard");
        router.refresh();
      } else if (response && response.mfa_required) {
        // Handle MFA requirement - status 202 is returned as success data by our request client
        setMfaState({ required: true, sessionId: response.session_id });
        showNotification(
          "MFA verification required. Please enter your authentication code.",
          "warning",
        );
      } else {
        throw new Error("Login failed: Invalid response format");
      }
    } catch (error) {
      // Re-throw or handle error
      const message =
        error instanceof Error ? error.message : "Authentication failed";
      throw new Error(message);
    }
  };

  const logout = async () => {
    await api.auth.logout();
    setUser(null);
    router.push("/login");
    router.refresh();
  };

  useEffect(() => {
    checkAuth();
  }, []);

  // Protected Route Logic + Desktop Auto-Redirect
  useEffect(() => {
    if (isLoading) return;
    const publicRoutes = ["/login", "/register", "/"];
    const isPublic = publicRoutes.some((p) => pathname?.startsWith(p));

    if (!user && !isPublic) {
      router.push("/login");
    }

    // Desktop "Zero-Login" Experience: If user is authenticated and on landing/login page, go to dashboard
    if (user && (pathname === "/" || pathname === "/login")) {
      router.push("/dashboard");
    }
  }, [user, isLoading, pathname, router]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        mfaState,
        login,
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

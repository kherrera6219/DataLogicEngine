'use client';

import { createContext, useContext, useEffect, useState, ReactNode, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { api, User } from '@/lib/api';
import { LoginCredentials } from '@/lib/api/auth';

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
    showNotification: (message: string, type: 'success' | 'error' | 'info' | 'warning') => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Notification event for cross-component communication
const NOTIFICATION_EVENT = 'auth-notification';

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [mfaState, setMfaState] = useState<MFAState>({ required: false });
    const router = useRouter();
    const pathname = usePathname();

    const showNotification = useCallback((message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') => {
        // Dispatch custom event that ToastProvider can listen to
        window.dispatchEvent(new CustomEvent(NOTIFICATION_EVENT, {
            detail: { message, type }
        }));
    }, []);

    const checkAuth = async () => {
        try {
            const data = await api.auth.check();
            if (data?.user) {
                setUser(data.user);
            } else {
                // If not authenticated, try desktop auto-login if on Windows
                // This is a "Zero-Config" experience for desktop users
                const autoLoginResponse = await api.auth.desktopAutoLogin().catch(() => null);
                if (autoLoginResponse && autoLoginResponse.success && autoLoginResponse.data.user) {
                    setUser(autoLoginResponse.data.user);
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
        const response = await api.auth.login(credentials);
        if (response.success && response.data.user) {
            setUser(response.data.user);
            router.push('/dashboard');
            router.refresh();
        } else if (response.status === 202) {
             // Handle MFA requirement
             setMfaState({ required: true, sessionId: response.data?.session_id });
             showNotification('MFA verification required. Please enter your authentication code.', 'warning');
        } else {
            throw new Error(response.error || 'Login failed');
        }
    };

    const logout = async () => {
        await api.auth.logout();
        setUser(null);
        router.push('/login');
        router.refresh();
    };

    useEffect(() => {
        checkAuth();
    }, []);

    // Protected Route Logic
    useEffect(() => {
        if (isLoading) return;
        const publicRoutes = ['/login', '/register', '/'];
        const isPublic = publicRoutes.some(p => pathname?.startsWith(p));
        
        if (!user && !isPublic) {
            router.push('/login');
        }
        
    }, [user, isLoading, pathname, router]);

    return (
        <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, mfaState, login, logout, checkAuth, showNotification }}>
            {children}
        </AuthContext.Provider>
    );
}

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};

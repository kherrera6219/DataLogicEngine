'use client';

import { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { api, User } from '@/lib/api';
import { LoginCredentials } from '@/lib/api/auth';

interface AuthContextType {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    login: (credentials: LoginCredentials) => Promise<void>;
    logout: () => Promise<void>;
    checkAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const router = useRouter();
    const pathname = usePathname();

    const checkAuth = async () => {
        try {
            const data = await api.auth.check();
            if (data?.user) {
                setUser(data.user);
            } else {
                setUser(null);
            }
        } catch {
            setUser(null);
        } finally {
            setIsLoading(false);
        }
    };

    const login = async (credentials: LoginCredentials) => {
            router.push('/dashboard');
            router.refresh();
        } else if (response.status === 202) {
             // Handle MFA (Placeholder)
             alert("MFA Required - Implementation Pending");
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
        <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, logout, checkAuth }}>
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

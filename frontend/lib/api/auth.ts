import { API_BASE, User } from './types';

export interface LoginCredentials {
    username?: string;
    email?: string;
    password: string;
}

export interface AuthCheckResponse {
    authenticated?: boolean;
    user?: User;
}

export interface LoginResponse {
    success: boolean;
    status?: number;
    data: {
        user: User;
        token?: string;
    };
    error?: string;
}

export const auth = {
    check: async (): Promise<AuthCheckResponse | null> => {
        try {
            const res = await fetch(`${API_BASE}/auth/check`);
            return await res.json();
        } catch(e) { return null; }
    },
    login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(credentials)
        });
        return await res.json();
    },
    logout: async (): Promise<void> => {
        await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
    }
};

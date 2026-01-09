import { API_BASE } from './types';

export const auth = {
    check: async () => {
        try {
            const res = await fetch(`${API_BASE}/auth/check`);
            return await res.json();
        } catch(e) { return null; }
    },
    login: async (credentials: any) => {
        const res = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(credentials)
        });
        return await res.json();
    },
    logout: async () => {
        await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
    }
};

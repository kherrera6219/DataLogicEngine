import { User } from './types';
import { request } from './client';

export interface AuthCheckResponse {
    authenticated?: boolean;
    user?: User;
}

export interface DesktopAuthResponse {
    user?: User;
    token?: string;
}

/**
 * Single-mode auth surface. The app runs with OS-level auth (Windows identity +
 * signed Electron loopback); there is no multi-user web login. The removed
 * `login`/`logout` methods called `/auth/login` and `/auth/logout`, which no
 * longer exist on the backend (see `backend/routes/auth_routes.py`). Only the
 * session check and the desktop auto-login handshake remain.
 */
export const auth = {
    check: (): Promise<AuthCheckResponse | null> =>
        request<AuthCheckResponse>('/auth/check').catch(() => ({ authenticated: false })),

    desktopAutoLogin: (): Promise<DesktopAuthResponse> =>
        request<DesktopAuthResponse>('/auth/desktop/auto-login', { method: 'POST' })
};

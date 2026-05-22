import { User } from './types';
import { request } from './client';

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
    user?: User;
    token?: string;
    mfa_required?: boolean;
    session_id?: string;
}

export const auth = {
    check: (): Promise<AuthCheckResponse | null> => 
        request<AuthCheckResponse>('/auth/check').catch(() => ({ authenticated: false })),
    
    login: (credentials: LoginCredentials): Promise<LoginResponse> => 
        request<LoginResponse>('/auth/login', {
            method: 'POST',
            body: JSON.stringify(credentials)
        }),
    
    logout: (): Promise<void> => 
        request('/auth/logout', { method: 'POST' }).then(() => {}).catch(() => {}),

    desktopAutoLogin: (): Promise<LoginResponse> =>
        request<LoginResponse>('/auth/desktop/auto-login', { method: 'POST' })
};


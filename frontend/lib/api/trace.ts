import { request } from './index';

export const trace = {
    list: (limit: number = 20) => request<unknown[]>(`/traces?limit=${limit}`),
    get: (id: string) => request<unknown>(`/traces/${id}`),
    export: (id: string) => request<Blob>(`/traces/${id}/export`).catch(() => null)
};

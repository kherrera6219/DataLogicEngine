import { API_BASE, PillarLevel } from './types';

export const knowledge = {
    pillars: async () => {
        try {
            const res = await fetch(`${API_BASE}/pillar-levels`);
            if (!res.ok) return [];
            const data = await res.json();
            return (data.success ? data.data : data) as PillarLevel[];
        } catch(e) { return []; }
    },
    stats: async () => {
        try {
           const res = await fetch(`${API_BASE}/pillar-levels`);
           return (await res.json()).data?.length || 0;
        } catch(e) { return 0; }
    }
};

import { API_BASE, SimulationSession } from './types';

export const simulation = {
    list: async () => {
        try {
          const res = await fetch(`${API_BASE}/simulations`);
          if (!res.ok) return [];
          const data = await res.json();
          return (data.success ? data.data : data) as SimulationSession[];
        } catch { return []; }
    },
    create: async (name: string, parameters: Record<string, unknown> = {}) => {
        const res = await fetch(`${API_BASE}/simulations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, parameters })
        });
        if (!res.ok) throw new Error("Failed to create simulation");
        const data = await res.json();
        return data.success ? data.data : data;
    },
    step: async (uid: string) => {
        const res = await fetch(`${API_BASE}/simulations/${uid}/step`, { method: 'POST' });
        return res.json();
    }
};

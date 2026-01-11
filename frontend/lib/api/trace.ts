import { API_BASE } from './types';

export const trace = {
  list: async (limit: number = 10) => {
     try {
       const res = await fetch(`${API_BASE}/trace/runs?limit=${limit}`);
       if (!res.ok) return [];
       const data = await res.json();
       if (data.success && Array.isArray(data.data)) return data.data;
       return Array.isArray(data) ? data : (data.runs || []);
     } catch {
       console.error("Failed to fetch traces");
       return undefined;
     }
  },
  get: async (id: string) => {
     try {
       const res = await fetch(`${API_BASE}/trace/runs/${id}`);
       if (!res.ok) return null;
       const data = await res.json();
       return data.success ? data.data : data; 
     } catch {
        return null;
     }
  }
};

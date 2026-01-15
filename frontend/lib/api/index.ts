
import { auth } from './auth';
import { simulation } from './simulation';
import { knowledge } from './knowledge';
import { trace } from './trace';
import { chat, sendChat } from './system_chat';
import { mcp } from './mcp';
import { compliance } from './compliance';

export * from './types';
export { sendChat };

// Base config
export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000/api/v1';

export const api = {
  chat,
  auth,
  simulation,
  knowledge,
  trace,
  mcp,
  compliance,
  analytics: {
    summary: async () => {
      const res = await fetch(`${API_BASE}/analytics/summary`);
      if (!res.ok) throw new Error("Failed to fetch analytics summary");
      const json = await res.json();
      return json.data;
    },
    trends: async (metric: string, days: number = 7) => {
      const res = await fetch(`${API_BASE}/analytics/trends?metric=${metric}&days=${days}`);
      if (!res.ok) throw new Error("Failed to fetch trends");
      return res.json();
    }
  }
};


import { API_BASE } from "./types";

export interface ComplianceStandard {
  uid: string;
  id: string;
  name: string;
  description: string;
  type: string;
}

export const compliance = {
  standards: async (type?: string) => {
    const url = type 
      ? `${API_BASE}/compliance/standards?type=${type}`
      : `${API_BASE}/compliance/standards`;
    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to fetch compliance standards");
    return res.json();
  },

  exportAuditLogs: async (days: number = 30) => {
      // Trigger download
      window.open(`${API_BASE}/compliance/audit/export?days=${days}`, '_blank');
  }
};

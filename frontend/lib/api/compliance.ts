import { request, buildApiUrl } from "./client";

export interface ComplianceStandard {
  uid: string;
  id: string;
  name: string;
  description: string;
  type: string;
}

export const compliance = {
  standards: (type?: string) => {
    const endpoint = type 
      ? `/compliance/standards?type=${type}`
      : `/compliance/standards`;
    return request(endpoint);
  },

  exportAuditLogs: async (days: number = 30) => {
      // Trigger download
      window.open(buildApiUrl(`/compliance/audit/export?days=${days}`), '_blank');
  }
};

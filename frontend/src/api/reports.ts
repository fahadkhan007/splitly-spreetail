import { apiClient } from './client';
import type { GroupSummaryReport, MonthlyReport } from './types';

export const reports = {
  getSummary: async (groupId: string) => {
    const { data } = await apiClient.get<GroupSummaryReport>(`/groups/${groupId}/reports/summary`);
    return data;
  },

  getMonthly: async (groupId: string) => {
    const { data } = await apiClient.get<MonthlyReport>(`/groups/${groupId}/reports/monthly`);
    return data;
  },
};

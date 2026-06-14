import { apiClient } from './client';
import type { GroupBalanceReport, MemberBalance } from './types';

export const balances = {
  getGroupBalances: async (groupId: string) => {
    const { data } = await apiClient.get<GroupBalanceReport>(`/groups/${groupId}/balances`);
    return data;
  },

  getMyBalances: async () => {
    const { data } = await apiClient.get<MemberBalance[]>('/balances/me');
    return data;
  },
};

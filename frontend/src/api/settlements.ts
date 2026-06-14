import { apiClient } from './client';
import type { SettlementOut, SettlementCreate } from './types';

export const settlements = {
  getSettlements: async (groupId: string, skip = 0, limit = 100) => {
    const { data } = await apiClient.get<SettlementOut[]>(`/groups/${groupId}/settlements`, {
      params: { skip, limit },
    });
    return data;
  },

  createSettlement: async (groupId: string, payload: SettlementCreate) => {
    const { data } = await apiClient.post<SettlementOut>(`/groups/${groupId}/settlements`, payload);
    return data;
  },

  voidSettlement: async (groupId: string, settlementId: string) => {
    const { data } = await apiClient.post<{ message: string; settlement: SettlementOut }>(
      `/groups/${groupId}/settlements/${settlementId}/void`
    );
    return data;
  },
};

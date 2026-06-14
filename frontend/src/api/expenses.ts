import { apiClient } from './client';
import type { ExpenseOut, ExpenseCreate } from './types';

export const expenses = {
  getExpenses: async (groupId: string, skip = 0, limit = 100) => {
    const { data } = await apiClient.get<ExpenseOut[]>(`/groups/${groupId}/expenses`, {
      params: { skip, limit },
    });
    return data;
  },

  createExpense: async (groupId: string, payload: ExpenseCreate) => {
    const { data } = await apiClient.post<ExpenseOut>(`/groups/${groupId}/expenses`, payload);
    return data;
  },

  deleteExpense: async (groupId: string, expenseId: string) => {
    const { data } = await apiClient.delete<{ message: string }>(`/groups/${groupId}/expenses/${expenseId}`);
    return data;
  },

  updateExpense: async (groupId: string, expenseId: string, payload: { description?: string; notes?: string; expense_date?: string }) => {
    const { data } = await apiClient.patch<ExpenseOut>(`/groups/${groupId}/expenses/${expenseId}`, payload);
    return data;
  },
};

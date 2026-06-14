import { apiClient } from './client';
import type { Group, GroupDetailOut, ImportReportOut, ImportSummaryOut, InvitationOut } from './types';

export const groups = {
  getGroups: async () => {
    const { data } = await apiClient.get<Group[]>('/groups');
    return data;
  },

  createGroup: async (name: string, description: string | null = null, baseCurrency: string = 'INR') => {
    const { data } = await apiClient.post<Group>('/groups', {
      name,
      description,
      base_currency: baseCurrency,
    });
    return data;
  },

  getGroupById: async (groupId: string) => {
    const { data } = await apiClient.get<GroupDetailOut>(`/groups/${groupId}`);
    return data;
  },

  updateGroup: async (groupId: string, name: string, description: string | null = null) => {
    const { data } = await apiClient.patch<GroupDetailOut>(`/groups/${groupId}`, {
      name,
      description
    });
    return data;
  },

  closeGroup: async (groupId: string) => {
    const { data } = await apiClient.delete<{ message: string }>(`/groups/${groupId}`);
    return data;
  },

  inviteMember: async (groupId: string, email: string) => {
    const { data } = await apiClient.post<{ message: string; invitation_id: string }>(
      `/groups/${groupId}/invitations`,
      { email }
    );
    return data;
  },

  getPendingInvites: async (groupId: string) => {
    const { data } = await apiClient.get<InvitationOut[]>(`/groups/${groupId}/invitations`);
    return data;
  },

  acceptInvite: async (token: string) => {
    const { data } = await apiClient.post<{ message: string }>(`/invitations/accept?token=${token}`);
    return data;
  },

  removeMember: async (groupId: string, userId: string) => {
    const { data } = await apiClient.delete<{ message: string }>(`/groups/${groupId}/members/${userId}`);
    return data;
  },

  leaveGroup: async (groupId: string) => {
    const { data } = await apiClient.post<{ message: string }>(`/groups/${groupId}/leave`);
    return data;
  },

  // Import endpoints
  uploadCsv: async (groupId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await apiClient.post<ImportReportOut>(
      `/groups/${groupId}/import`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  },

  getImportReports: async (groupId: string) => {
    const { data } = await apiClient.get<ImportSummaryOut[]>(`/groups/${groupId}/imports`);
    return data;
  },

  getImportReportById: async (groupId: string, importId: string) => {
    const { data } = await apiClient.get<ImportReportOut>(`/groups/${groupId}/imports/${importId}`);
    return data;
  },
};

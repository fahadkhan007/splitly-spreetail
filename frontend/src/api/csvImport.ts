import { apiClient } from './client';
import type { ImportReportOut, ImportSummaryOut } from './types';

export const csvImport = {
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

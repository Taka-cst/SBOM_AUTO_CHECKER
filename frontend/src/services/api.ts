import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// SBOM API
export const sbomApi = {
  // SBOMファイルをアップロード
  upload: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API_BASE_URL}/api/v1/sbom/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // SBOM一覧を取得
  getAll: async (page = 1, limit = 20) => {
    const response = await apiClient.get('/api/v1/sbom', {
      params: { page, limit },
    });
    return response.data;
  },

  // SBOM詳細を取得
  getById: async (id: string) => {
    const response = await apiClient.get(`/api/v1/sbom/${id}`);
    return response.data;
  },

  // SBOMを削除
  delete: async (id: string) => {
    const response = await apiClient.delete(`/api/v1/sbom/${id}`);
    return response.data;
  },
};

// スキャン API
export const scanApi = {
  // スキャン結果を取得
  getResult: async (sbomId: string) => {
    const response = await apiClient.get(`/api/v1/scan/${sbomId}/result`);
    return response.data.data; // バックエンドのレスポンス構造に合わせて修正
  },

  // スキャン履歴を取得
  getHistory: async (page = 1, limit = 20) => {
    const response = await apiClient.get('/api/v1/scan/history', {
      params: { page, limit },
    });
    return response.data;
  },

  // 再スキャンを実行
  rescan: async (sbomId: string) => {
    const response = await apiClient.post(`/api/v1/scan/${sbomId}/rescan`);
    return response.data;
  },

  // レポートをエクスポート
  exportReport: async (sbomId: string, format: 'json' | 'csv') => {
    const response = await axios.get(`${API_BASE_URL}/api/v1/scan/${sbomId}/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },

  // サマリーを取得
  getSummary: async (sbomId: string) => {
    const response = await apiClient.get(`/api/v1/scan/${sbomId}/summary`);
    return response.data;
  },
};

// 統計 API
export const statsApi = {
  // 全体統計を取得
  getOverview: async () => {
    const response = await apiClient.get('/api/v1/stats/overview');
    return response.data;
  },

  // トレンドデータを取得
  getTrends: async (period = '30d') => {
    const response = await apiClient.get('/api/v1/stats/trends', {
      params: { period },
    });
    return response.data;
  },
};

// ヘルスチェック
export const healthCheck = async () => {
  const response = await axios.get(`${API_BASE_URL}/health`);
  return response.data;
};

export default apiClient;

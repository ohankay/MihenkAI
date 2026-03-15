import axios, { AxiosInstance, AxiosError } from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';

const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Error handler
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export interface ApiError {
  detail?: string;
  [key: string]: any;
}

// Config endpoints
export const configAPI = {
  getConfig: async () => {
    const response = await api.get('/config');
    return response.data;
  },
  


  getStatus: async () => {
    const response = await api.get('/status');
    return response.data;
  },
};

// Model config endpoints
export const modelAPI = {
  list: async () => {
    const response = await api.get('/model-configs');
    return response.data;
  },

  get: async (id: number) => {
    const response = await api.get(`/model-configs/${id}`);
    return response.data;
  },

  create: async (data: {
    provider: string;
    model_name: string;
    api_key?: string;
    base_url?: string;
    temperature?: number;
    generation_kwargs?: Record<string, any>;
  }) => {
    const response = await api.post('/model-configs', data);
    return response.data;
  },

  update: async (id: number, data: Partial<any>) => {
    const response = await api.put(`/model-configs/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    const response = await api.delete(`/model-configs/${id}`);
    return response.data;
  },
};

// Profile endpoints
export const profileAPI = {
  list: async () => {
    const response = await api.get('/profiles');
    return response.data;
  },

  get: async (id: number) => {
    const response = await api.get(`/profiles/${id}`);
    return response.data;
  },

  create: async (data: {
    name: string;
    description?: string;
    model_config_id: number;
    single_weights: Record<string, number>;
    conversational_weights: Record<string, number>;
  }) => {
    const response = await api.post('/profiles', data);
    return response.data;
  },

  update: async (id: number, data: Partial<any>) => {
    const response = await api.put(`/profiles/${id}`, data);
    return response.data;
  },

  delete: async (id: number) => {
    const response = await api.delete(`/profiles/${id}`);
    return response.data;
  },
};

// Evaluation endpoints
export const evaluationAPI = {
  startSingle: async (data: {
    profile_id: number;
    prompt: string;
    actual_response: string;
    retrieved_contexts: string[];
    expected_response?: string;
  }) => {
    const response = await api.post('/evaluate/single', data);
    return response.data;
  },

  startConversational: async (data: {
    profile_id: number;
    chat_history: Array<{ role: string; content: string }>;
    prompt: string;
    actual_response: string;
    retrieved_contexts: string[];
  }) => {
    const response = await api.post('/evaluate/conversational', data);
    return response.data;
  },

  getStatus: async (jobId: string) => {
    const response = await api.get(`/evaluate/status/${jobId}`);
    return response.data;
  },

  listJobs: async (limit = 50, offset = 0) => {
    const response = await api.get('/evaluate/jobs', {
      params: { limit, offset },
    });
    return response.data;
  },
};

export default api;

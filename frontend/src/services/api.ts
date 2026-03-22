import axios, { AxiosInstance, AxiosError } from 'axios';

// VITE_API_BASE_URL is only meaningful when explicitly set as a build arg.
// Fallback: use the same hostname the browser used to reach the frontend,
// so the app works from any machine on the network (not just localhost).
const API_BASE_URL =
  (import.meta.env.VITE_API_BASE_URL as string) ||
  `http://${window.location.hostname}:8000`;

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

export interface EvaluationJobSummary {
  job_id: string;
  profile_id: number;
  evaluation_type: string;
  status: string;
  composite_score?: number | null;
  error_message?: string | null;
  created_at: string;
  completed_at?: string | null;
}

export interface EvaluationJobListResponse {
  items: EvaluationJobSummary[];
  jobs?: EvaluationJobSummary[];
  limit: number;
  offset: number;
  count: number;
  total: number;
  has_next: boolean;
}

export interface EvaluationJobDetail extends EvaluationJobSummary {
  metrics_breakdown?: Record<string, Record<string, any>> | null;
  request_payload?: Record<string, any> | null;
  result_payload?: Record<string, any> | null;
}

export interface AbortJobsResponse {
  aborted_job_ids: string[];
  skipped_job_ids: string[];
  not_found_job_ids: string[];
}

export interface ModelChatTestResponse {
  model_config_id: number;
  provider: string;
  model_name: string;
  prompt: string;
  response: string;
  latency_ms: number;
}

export interface LLMQueryLogSummary {
  id: number;
  model_config_id: number;
  created_at: string;
  latency_ms?: number | null;
  error_message?: string | null;
}

export interface LLMQueryLogListResponse {
  items: LLMQueryLogSummary[];
  limit: number;
  offset: number;
  count: number;
  total: number;
  has_next: boolean;
  start_time: string;
  end_time: string;
}

export interface LLMQueryLogDetail {
  id: number;
  model_config_id: number;
  prompt: string;
  response?: string | null;
  latency_ms?: number | null;
  error_message?: string | null;
  created_at: string;
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
    name: string;
    provider: string;
    model_name: string;
    api_key?: string;
    base_url?: string;
    temperature?: number;
    generation_kwargs?: Record<string, any>;
    system_prompt?: string;
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

  testChat: async (id: number, prompt: string) => {
    const response = await api.post(`/model-configs/${id}/test-chat`, { prompt });
    return response.data as ModelChatTestResponse;
  },

  listQueryLogs: async (id: number, params: { limit?: number; offset?: number; start_time?: string; end_time?: string }) => {
    const response = await api.get(`/model-configs/${id}/query-logs`, { params });
    return response.data as LLMQueryLogListResponse;
  },

  getQueryLogDetail: async (id: number, logId: number) => {
    const response = await api.get(`/model-configs/${id}/query-logs/${logId}`);
    return response.data as LLMQueryLogDetail;
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
    single_weights: Record<string, number>;
    single_negative_thresholds?: Record<string, number>;
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
    evaluation_profile_id: number;
    judge_llm_profile_id: number;
    prompt: string;
    actual_response: string;
    retrieved_contexts: string[];
    expected_response: string;
  }) => {
    const response = await api.post('/evaluate/single', data);
    return response.data;
  },

  startConversational: async (data: {
    evaluation_profile_id: number;
    judge_llm_profile_id: number;
    chat_history: Array<{ role: string; content: string }>;
    prompt: string;
    actual_response: string;
    retrieved_contexts: string[];
    scenario?: string;
    expected_outcome?: string;
  }) => {
    const response = await api.post('/evaluate/conversational', data);
    return response.data;
  },

  getStatus: async (jobId: string) => {
    const response = await api.get(`/evaluate/status/${jobId}`);
    return response.data;
  },

  listJobs: async (
    params: {
      limit?: number;
      offset?: number;
      profile_id?: number;
      status?: string;
      start_time?: string;
      end_time?: string;
    } = {}
  ) => {
    const response = await api.get('/evaluate/jobs', {
      params: { limit: 50, offset: 0, ...params },
    });
    return response.data as EvaluationJobListResponse;
  },

  getJobDetail: async (jobId: string) => {
    const response = await api.get(`/evaluate/jobs/${jobId}`);
    return response.data as EvaluationJobDetail;
  },

  abortJobs: async (jobIds: string[]) => {
    const response = await api.post('/evaluate/jobs/abort', {
      job_ids: jobIds,
    });
    return response.data as AbortJobsResponse;
  },

  abortJob: async (jobId: string) => {
    const response = await api.post(`/evaluate/jobs/${jobId}/abort`);
    return response.data as AbortJobsResponse;
  },
};

export default api;

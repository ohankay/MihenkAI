import React, { createContext, useContext, useState, ReactNode } from 'react';

export interface ModelConfig {
  id: number;
  provider: string;
  model_name: string;
  temperature: number;
  created_at: string;
}

export interface EvaluationProfile {
  id: number;
  name: string;
  description?: string;
  model_config_id: number;
  single_weights: Record<string, number>;
  conversational_weights: Record<string, number>;
  created_at: string;
}

export interface EvaluationJob {
  job_id: string;
  status: string;
  composite_score?: number;
  metrics_breakdown?: Record<string, { score: number; weight: number }>;
  error_message?: string;
  created_at: string;
  completed_at?: string;
}

export interface ConfigData {
  connected: boolean;
}

interface AppContextType {
  // Config
  config: ConfigData | null;
  isConfigured: boolean;
  setConfig: (config: ConfigData) => void;

  // Models
  modelConfigs: ModelConfig[];
  addModelConfig: (config: ModelConfig) => void;
  removeModelConfig: (id: number) => void;
  setModelConfigs: (configs: ModelConfig[]) => void;

  // Profiles
  profiles: EvaluationProfile[];
  addProfile: (profile: EvaluationProfile) => void;
  updateProfile: (profile: EvaluationProfile) => void;
  removeProfile: (id: number) => void;
  setProfiles: (profiles: EvaluationProfile[]) => void;

  // Evaluation Jobs
  currentJob: EvaluationJob | null;
  setCurrentJob: (job: EvaluationJob | null) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [config, setConfig] = useState<ConfigData | null>(null);
  const [isConfigured, setIsConfigured] = useState(false);
  const [modelConfigs, setModelConfigs] = useState<ModelConfig[]>([]);
  const [profiles, setProfiles] = useState<EvaluationProfile[]>([]);
  const [currentJob, setCurrentJob] = useState<EvaluationJob | null>(null);

  const addModelConfig = (config: ModelConfig) => {
    setModelConfigs([...modelConfigs, config]);
  };

  const removeModelConfig = (id: number) => {
    setModelConfigs(modelConfigs.filter(c => c.id !== id));
  };

  const addProfile = (profile: EvaluationProfile) => {
    setProfiles([...profiles, profile]);
  };

  const updateProfile = (profile: EvaluationProfile) => {
    setProfiles(profiles.map(p => p.id === profile.id ? profile : p));
  };

  const removeProfile = (id: number) => {
    setProfiles(profiles.filter(p => p.id !== id));
  };

  const value: AppContextType = {
    config,
    isConfigured,
    setConfig: (cfg) => {
      setConfig(cfg);
      setIsConfigured(true);
    },
    modelConfigs,
    addModelConfig,
    removeModelConfig,
    setModelConfigs,
    profiles,
    addProfile,
    updateProfile,
    removeProfile,
    setProfiles,
    currentJob,
    setCurrentJob,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};

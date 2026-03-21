import React, { useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { modelAPI } from '../services/api';
import { useForm } from '../hooks/useCustom';
import AppShell from '../components/AppShell';

const PROVIDER_DEFAULTS: Record<string, { base_url: string; model_placeholder: string }> = {
  OpenAI:    { base_url: '',                                                                   model_placeholder: 'e.g., gpt-4o, gpt-4-turbo' },
  Anthropic: { base_url: '',                                                                   model_placeholder: 'e.g., claude-3-5-sonnet-20241022' },
  Gemini:    { base_url: 'https://generativelanguage.googleapis.com/v1beta/openai/',           model_placeholder: 'e.g., gemini-2.0-flash' },
  Grok:      { base_url: 'https://api.x.ai/v1',                                               model_placeholder: 'e.g., grok-2, grok-3' },
  DeepSeek:  { base_url: 'https://api.deepseek.com/v1',                                       model_placeholder: 'e.g., deepseek-chat, deepseek-reasoner' },
  Ollama:    { base_url: 'http://host.docker.internal:11434/v1',                              model_placeholder: 'e.g., llama3, mistral' },
  vLLM:      { base_url: 'http://host.docker.internal:8080/v1',                               model_placeholder: 'e.g., mistralai/Mistral-7B-v0.1' },
};

const Models: React.FC = () => {
  const { modelConfigs, setModelConfigs, addModelConfig, removeModelConfig } = useApp();
  const [loading, setLoading] = React.useState(false);
  const [showForm, setShowForm] = React.useState(false);
  const [editingId, setEditingId] = React.useState<number | null>(null);
  const [editingHasApiKey, setEditingHasApiKey] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const [genKwargsError, setGenKwargsError] = React.useState<string | null>(null);

  useEffect(() => {
    loadModels();
  }, []);

  const loadModels = async () => {
    try {
      setLoading(true);
      const configs = await modelAPI.list();
      setModelConfigs(configs);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load models');
    } finally {
      setLoading(false);
    }
  };

  const form = useForm(
    {
      name: '',
      provider: '',
      model_name: '',
      api_key: '',
      base_url: '',
      temperature: 0.0,
      generation_kwargs: '',
      system_prompt: '',
    },
    async (values) => {
      try {
        let generation_kwargs: Record<string, any> | undefined = undefined;
        if (values.generation_kwargs.trim()) {
          try {
            generation_kwargs = JSON.parse(values.generation_kwargs);
          } catch {
            setGenKwargsError('Invalid JSON format');
            return;
          }
        }
        setGenKwargsError(null);
        const payload = { ...values, generation_kwargs };
        if (editingId !== null) {
          const updatePayload = { ...payload, api_key: values.api_key || undefined };
          const updated = await modelAPI.update(editingId, updatePayload);
          setModelConfigs(modelConfigs.map((c) => (c.id === editingId ? updated : c)));
          setEditingId(null);
        } else {
          const newConfig = await modelAPI.create(payload);
          addModelConfig(newConfig);
        }
        form.reset();
        setShowForm(false);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to save model');
      }
    }
  );

  const handleEdit = (config: any) => {
    setEditingId(config.id);
    setEditingHasApiKey(!!config.has_api_key);
    form.setValues({
      name: config.name || '',
      provider: config.provider,
      model_name: config.model_name,
      api_key: '',
      base_url: config.base_url || '',
      temperature: config.temperature,
      generation_kwargs: config.generation_kwargs
        ? JSON.stringify(config.generation_kwargs, null, 2)
        : '',
      system_prompt: config.system_prompt || '',
    });
    setShowForm(true);
    setError(null);
  };

  const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const provider = e.target.value;
    const defaults = PROVIDER_DEFAULTS[provider];
    form.setValues({
      ...form.values,
      provider,
      // Auto-fill base_url only when the field is still empty (don't overwrite user input)
      base_url: form.values.base_url || (defaults?.base_url ?? ''),
    });
  };

  const handleClone = (config: any) => {
    setEditingId(null);
    setEditingHasApiKey(false);
    form.setValues({
      name: `Copy of ${config.name || config.model_name}`,
      provider: config.provider,
      model_name: config.model_name,
      api_key: '',
      base_url: config.base_url || '',
      temperature: config.temperature,
      generation_kwargs: config.generation_kwargs
        ? JSON.stringify(config.generation_kwargs, null, 2)
        : '',
      system_prompt: config.system_prompt || '',
    });
    setShowForm(true);
    setError(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingId(null);
    setEditingHasApiKey(false);
    form.reset();
    setError(null);
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure?')) {
      try {
        await modelAPI.delete(id);
        removeModelConfig(id);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to delete model');
      }
    }
  };

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-stone-800 mb-6">Judge LLM Profiles</h1>

        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <button
          onClick={() => { if (showForm) { handleCancelForm(); } else { setShowForm(true); } }}
          className="mb-6 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-md transition font-medium"
        >
          {showForm ? 'Cancel' : 'New Judge LLM Profile'}
        </button>

        {showForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">{editingId !== null ? 'Edit Judge LLM Profile' : 'New Judge LLM Profile'}</h2>
            <form onSubmit={form.handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-stone-700">Judge LLM Profile Name</label>
                <input
                  type="text"
                  name="name"
                  value={form.values.name}
                  onChange={form.handleChange}
                  placeholder="e.g., GPT-4o Strict, Claude Low Temp"
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-stone-700">Provider</label>
                <select
                  name="provider"
                  value={form.values.provider}
                  onChange={handleProviderChange}
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500 bg-white"
                  required
                >
                  <option value="">— select provider —</option>
                  <option value="OpenAI">OpenAI</option>
                  <option value="Anthropic">Anthropic</option>
                  <option value="Gemini">Gemini</option>
                  <option value="Grok">Grok</option>
                  <option value="DeepSeek">DeepSeek</option>
                  <option value="Ollama">Ollama</option>
                  <option value="vLLM">vLLM</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-stone-700">Model Name</label>
                <input
                  type="text"
                  name="model_name"
                  value={form.values.model_name}
                  onChange={form.handleChange}
                  placeholder={PROVIDER_DEFAULTS[form.values.provider]?.model_placeholder ?? 'e.g., gpt-4o, llama3'}
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-stone-700">API Key (optional)</label>
                <input
                  type="password"
                  name="api_key"
                  value={form.values.api_key}
                  onChange={form.handleChange}
                  placeholder={editingHasApiKey && !form.values.api_key ? '••••••••  (saved)' : ''}
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
                {editingHasApiKey && (
                  <p className="mt-1 text-xs text-stone-400">Boş bırakılırsa mevcut API key korunur.</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-stone-700">Base URL (optional)</label>
                <input
                  type="text"
                  name="base_url"
                  value={form.values.base_url}
                  onChange={form.handleChange}
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-stone-700">Temperature</label>
                <input
                  type="number"
                  name="temperature"
                  value={form.values.temperature}
                  onChange={form.handleChange}
                  min="0"
                  max="2"
                  step="0.1"
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-stone-700">
                  System Prompt (optional)
                </label>
                <textarea
                  name="system_prompt"
                  value={form.values.system_prompt}
                  onChange={form.handleChange}
                  rows={5}
                  placeholder="e.g., You are a strict evaluation judge. Always respond in JSON format."
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500 text-sm"
                />
                <p className="mt-1 text-xs text-stone-400">Bu metin her LLM çağrısında sistem mesajı olarak eklenecektir.</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-stone-700">
                  Generation Parameters (optional, JSON)
                </label>
                <textarea
                  name="generation_kwargs"
                  value={form.values.generation_kwargs}
                  onChange={form.handleChange}
                  rows={6}
                  placeholder={`e.g.\n{\n  "max_tokens": 2000,\n  "top_p": 0.95,\n  "frequency_penalty": 0.0,\n  "presence_penalty": 0.0,\n  "timeout": 30\n}`}
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500 font-mono text-sm"
                />
                {genKwargsError && (
                  <p className="mt-1 text-sm text-red-600">{genKwargsError}</p>
                )}
              </div>

              <button
                type="submit"
                disabled={form.isSubmitting}
                className="w-full bg-amber-500 hover:bg-amber-600 text-white font-semibold py-2 rounded-md transition disabled:opacity-50"
              >
                {form.isSubmitting ? 'Saving...' : editingId !== null ? 'Save Changes' : 'Create Profile'}
              </button>
            </form>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-stone-50 border-b border-stone-200">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-stone-700">ID</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-stone-700">Profile Name</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-stone-700">Provider</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-stone-700">Model Name</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-stone-700">Temperature</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-stone-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-stone-400">Loading...</td>
                </tr>
              ) : modelConfigs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-stone-400">No judge LLM profiles configured yet</td>
                </tr>
              ) : (
                modelConfigs.map((config) => (
                  <tr key={config.id} className="border-b border-stone-100 hover:bg-stone-50">
                    <td className="px-6 py-4 text-sm text-stone-400 font-mono">#{config.id}</td>
                    <td className="px-6 py-4 text-sm font-medium text-stone-900">{config.name || '—'}</td>
                    <td className="px-6 py-4 text-sm text-stone-700">{config.provider}</td>
                    <td className="px-6 py-4 text-sm text-stone-700">{config.model_name}</td>
                    <td className="px-6 py-4 text-sm text-stone-700">{config.temperature}</td>
                    <td className="px-6 py-4 text-sm flex gap-4">
                      <button
                        onClick={() => handleEdit(config)}
                        className="text-amber-600 hover:text-amber-800 font-medium"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleClone(config)}
                        className="text-stone-500 hover:text-stone-700 font-medium"
                      >
                        Clone
                      </button>
                      <button
                        onClick={() => handleDelete(config.id)}
                        className="text-red-500 hover:text-red-700 font-medium"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
};

export default Models;

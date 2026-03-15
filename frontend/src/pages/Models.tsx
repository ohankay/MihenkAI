import React, { useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { modelAPI } from '../services/api';
import { useForm } from '../hooks/useCustom';
import { Link } from 'react-router-dom';

const Models: React.FC = () => {
  const { modelConfigs, setModelConfigs, addModelConfig, removeModelConfig } = useApp();
  const [loading, setLoading] = React.useState(false);
  const [showForm, setShowForm] = React.useState(false);
  const [editingId, setEditingId] = React.useState<number | null>(null);
  const [error, setError] = React.useState<string | null>(null);

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
      provider: 'OpenAI',
      model_name: '',
      api_key: '',
      base_url: '',
      temperature: 0.0,
    },
    async (values) => {
      try {
        if (editingId !== null) {
          // Don't overwrite api_key if left blank during edit
          const payload = { ...values, api_key: values.api_key || undefined };
          const updated = await modelAPI.update(editingId, payload);
          setModelConfigs(modelConfigs.map((c) => (c.id === editingId ? updated : c)));
          setEditingId(null);
        } else {
          const newConfig = await modelAPI.create(values);
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
    form.setValues({
      provider: config.provider,
      model_name: config.model_name,
      api_key: '',
      base_url: config.base_url || '',
      temperature: config.temperature,
    });
    setShowForm(true);
    setError(null);
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingId(null);
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
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <Link to="/" className="text-blue-600 hover:text-blue-700 mb-4 inline-block">← Back</Link>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Model Configuration</h1>

        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <button
          onClick={() => { if (showForm) { handleCancelForm(); } else { setShowForm(true); } }}
          className="mb-6 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
        >
          {showForm ? 'Cancel' : 'Add Model'}
        </button>

        {showForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">{editingId !== null ? 'Edit Model Configuration' : 'New Model Configuration'}</h2>
            <form onSubmit={form.handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Provider</label>
                <input
                  type="text"
                  name="provider"
                  value={form.values.provider}
                  onChange={form.handleChange}
                  placeholder="e.g., OpenAI, Anthropic, Ollama"
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Model Name</label>
                <input
                  type="text"
                  name="model_name"
                  value={form.values.model_name}
                  onChange={form.handleChange}
                  placeholder="e.g., gpt-4o, llama3"
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">API Key (optional)</label>
                <input
                  type="password"
                  name="api_key"
                  value={form.values.api_key}
                  onChange={form.handleChange}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Base URL (optional)</label>
                <input
                  type="text"
                  name="base_url"
                  value={form.values.base_url}
                  onChange={form.handleChange}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Temperature</label>
                <input
                  type="number"
                  name="temperature"
                  value={form.values.temperature}
                  onChange={form.handleChange}
                  min="0"
                  max="2"
                  step="0.1"
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                />
              </div>

              <button
                type="submit"
                disabled={form.isSubmitting}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-md transition disabled:opacity-50"
              >
                {form.isSubmitting ? 'Saving...' : editingId !== null ? 'Save Changes' : 'Create Model'}
              </button>
            </form>
          </div>
        )}

        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Provider</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Model Name</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Temperature</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={4} className="px-6 py-4 text-center text-gray-500">Loading...</td>
                </tr>
              ) : modelConfigs.length === 0 ? (
                <tr>
                  <td colSpan={4} className="px-6 py-4 text-center text-gray-500">No models configured</td>
                </tr>
              ) : (
                modelConfigs.map((config) => (
                  <tr key={config.id} className="border-b hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">{config.provider}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{config.model_name}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{config.temperature}</td>
                    <td className="px-6 py-4 text-sm flex gap-4">
                      <button
                        onClick={() => handleEdit(config)}
                        className="text-blue-600 hover:text-blue-700 font-medium"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(config.id)}
                        className="text-red-600 hover:text-red-700 font-medium"
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
    </div>
  );
};

export default Models;

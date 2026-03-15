import React, { useEffect } from 'react';
import { useApp } from '../context/AppContext';
import { profileAPI, modelAPI } from '../services/api';
import { useForm } from '../hooks/useCustom';
import { Link } from 'react-router-dom';

const Profiles: React.FC = () => {
  const { profiles, setProfiles, addProfile, removeProfile, modelConfigs, setModelConfigs } = useApp();
  const [loading, setLoading] = React.useState(false);
  const [showForm, setShowForm] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [profs, models] = await Promise.all([profileAPI.list(), modelAPI.list()]);
      setProfiles(profs);
      setModelConfigs(models);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const form = useForm(
    {
      name: '',
      description: '',
      model_config_id: modelConfigs.length > 0 ? modelConfigs[0].id : 0,
      single_weights: { faithfulness: 0.6, answer_relevancy: 0.4 },
      conversational_weights: { knowledge_retention: 0.5, conversation_completeness: 0.5 },
    },
    async (values) => {
      try {
        // Validate weights
        const singleSum = Object.values(values.single_weights).reduce((a, b) => a + b, 0);
        const conversationalSum = Object.values(values.conversational_weights).reduce((a, b) => a + b, 0);

        if (!(0.99 <= singleSum && singleSum <= 1.01)) {
          setError(`Single weights must sum to 1.0 (current: ${singleSum.toFixed(2)})`);
          return;
        }

        if (!(0.99 <= conversationalSum && conversationalSum <= 1.01)) {
          setError(`Conversational weights must sum to 1.0 (current: ${conversationalSum.toFixed(2)})`);
          return;
        }

        const newProfile = await profileAPI.create({
          ...values,
          model_config_id: Number(values.model_config_id),
        });
        addProfile(newProfile);
        form.reset();
        setShowForm(false);
        setError(null);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to create profile');
      }
    }
  );

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure?')) {
      try {
        await profileAPI.delete(id);
        removeProfile(id);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to delete profile');
      }
    }
  };

  const handleWeightChange = (type: 'single' | 'conversational', metric: string, value: number) => {
    const field = type === 'single' ? 'single_weights' : 'conversational_weights';
    const current = form.values[field] as Record<string, number>;
    const newWeights = { ...current, [metric]: value };
    form.setFieldValue(field, newWeights);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <Link to="/" className="text-blue-600 hover:text-blue-700 mb-4 inline-block">← Back</Link>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Evaluation Profiles</h1>

        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <button
          onClick={() => setShowForm(!showForm)}
          className="mb-6 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition"
        >
          {showForm ? 'Cancel' : 'Create Profile'}
        </button>

        {showForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">New Profile</h2>
            <form onSubmit={form.handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700">Profile Name</label>
                <input
                  type="text"
                  name="name"
                  value={form.values.name}
                  onChange={form.handleChange}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  name="description"
                  value={form.values.description}
                  onChange={form.handleChange}
                  rows={3}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Judge Model</label>
                <select
                  name="model_config_id"
                  value={form.values.model_config_id}
                  onChange={form.handleChange}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                >
                  {modelConfigs.map((model) => (
                    <option key={model.id} value={model.id}>
                      {model.provider} - {model.model_name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Single Weights */}
              <div className="border-t pt-4">
                <h3 className="font-semibold text-gray-700 mb-3">Single Test Weights</h3>
                <div className="space-y-3">
                  {Object.entries(form.values.single_weights).map(([metric, weight]) => (
                    <div key={metric} className="flex items-center">
                      <label className="flex-1 text-sm text-gray-700">{metric}</label>
                      <input
                        type="number"
                        value={weight}
                        onChange={(e) => handleWeightChange('single', metric, parseFloat(e.target.value))}
                        min="0"
                        max="1"
                        step="0.1"
                        className="w-20 px-3 py-1 border border-gray-300 rounded-md"
                      />
                    </div>
                  ))}
                  <div className="text-sm text-gray-600 mt-2">
                    Sum: {Object.values(form.values.single_weights).reduce((a, b) => a + b, 0).toFixed(2)}
                  </div>
                </div>
              </div>

              {/* Conversational Weights */}
              <div className="border-t pt-4">
                <h3 className="font-semibold text-gray-700 mb-3">Conversational Test Weights</h3>
                <div className="space-y-3">
                  {Object.entries(form.values.conversational_weights).map(([metric, weight]) => (
                    <div key={metric} className="flex items-center">
                      <label className="flex-1 text-sm text-gray-700">{metric}</label>
                      <input
                        type="number"
                        value={weight}
                        onChange={(e) => handleWeightChange('conversational', metric, parseFloat(e.target.value))}
                        min="0"
                        max="1"
                        step="0.1"
                        className="w-20 px-3 py-1 border border-gray-300 rounded-md"
                      />
                    </div>
                  ))}
                  <div className="text-sm text-gray-600 mt-2">
                    Sum: {Object.values(form.values.conversational_weights).reduce((a, b) => a + b, 0).toFixed(2)}
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={form.isSubmitting}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-md transition disabled:opacity-50"
              >
                {form.isSubmitting ? 'Creating...' : 'Create Profile'}
              </button>
            </form>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {loading ? (
            <div className="text-center text-gray-500">Loading...</div>
          ) : profiles.length === 0 ? (
            <div className="text-center text-gray-500 col-span-2">No profiles created yet</div>
          ) : (
            profiles.map((profile) => (
              <div key={profile.id} className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900">{profile.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{profile.description}</p>
                <div className="mt-4 text-sm text-gray-700">
                  <div>Single: {Object.values(profile.single_weights).reduce((a, b) => a + b, 0).toFixed(2)}</div>
                  <div>Conv: {Object.values(profile.conversational_weights).reduce((a, b) => a + b, 0).toFixed(2)}</div>
                </div>
                <button
                  onClick={() => handleDelete(profile.id)}
                  className="mt-4 text-red-600 hover:text-red-700 font-medium text-sm"
                >
                  Delete
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Profiles;

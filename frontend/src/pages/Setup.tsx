import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from '../hooks/useCustom';
import { configAPI } from '../services/api';
import { useApp } from '../context/AppContext';

const Setup: React.FC = () => {
  const navigate = useNavigate();
  const { setConfig } = useApp();
  const [submitError, setSubmitError] = React.useState<string | null>(null);

  const form = useForm(
    {
      db_host: 'db',
      db_port: 5432,
      db_user: 'mihenkai_user',
      db_password: 'secure_password',
      db_name: 'mihenkai_db',
      redis_host: 'redis',
      redis_port: 6379,
    },
    async (values) => {
      try {
        setSubmitError(null);
        await configAPI.postConfig(values);
        setConfig(values);
        navigate('/');
      } catch (error: any) {
        setSubmitError(error.response?.data?.detail || 'Failed to save configuration');
      }
    }
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        <h1 className="text-3xl font-bold text-center mb-2 text-gray-800">MihenkAI</h1>
        <p className="text-center text-gray-600 mb-6">LLM Evaluation System</p>
        <p className="text-center text-gray-500 mb-8 text-sm">Initial Configuration Wizard</p>

        {submitError && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {submitError}
          </div>
        )}

        <form onSubmit={form.handleSubmit} className="space-y-4">
          {/* Database Section */}
          <div className="border-b pb-4 mb-4">
            <h3 className="font-semibold text-gray-700 mb-3">Database Configuration</h3>

            <div>
              <label className="block text-sm font-medium text-gray-700">Database Host</label>
              <input
                type="text"
                name="db_host"
                value={form.values.db_host}
                onChange={form.handleChange}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-2 mt-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Port</label>
                <input
                  type="number"
                  name="db_port"
                  value={form.values.db_port}
                  onChange={form.handleChange}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700">Username</label>
              <input
                type="text"
                name="db_user"
                value={form.values.db_user}
                onChange={form.handleChange}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
              />
            </div>

            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700">Password</label>
              <input
                type="password"
                name="db_password"
                value={form.values.db_password}
                onChange={form.handleChange}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
              />
            </div>

            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700">Database Name</label>
              <input
                type="text"
                name="db_name"
                value={form.values.db_name}
                onChange={form.handleChange}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Redis Section */}
          <div className="pb-4">
            <h3 className="font-semibold text-gray-700 mb-3">Redis Configuration</h3>

            <div>
              <label className="block text-sm font-medium text-gray-700">Redis Host</label>
              <input
                type="text"
                name="redis_host"
                value={form.values.redis_host}
                onChange={form.handleChange}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
              />
            </div>

            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700">Port</label>
              <input
                type="number"
                name="redis_port"
                value={form.values.redis_port}
                onChange={form.handleChange}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={form.isSubmitting}
            className="w-full mt-6 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-md transition duration-200 disabled:opacity-50"
          >
            {form.isSubmitting ? 'Saving...' : 'Save Configuration'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Setup;

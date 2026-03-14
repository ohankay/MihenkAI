import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { evaluationAPI, profileAPI } from '../services/api';
import { Link } from 'react-router-dom';

const Evaluation: React.FC = () => {
  const navigate = useNavigate();
  const { setCurrentJob, profiles, setProfiles } = useApp();
  const [activeTab, setActiveTab] = useState<'single' | 'conversational'>('single');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Single evaluation state
  const [singleForm, setSingleForm] = useState({
    profile_id: 0,
    prompt: '',
    actual_response: '',
    retrieved_contexts: [''],
    expected_response: '',
  });

  // Conversational evaluation state
  const [conversationalForm, setConversationalForm] = useState({
    profile_id: 0,
    chat_history: [{ role: 'user', content: '' }],
    prompt: '',
    actual_response: '',
    retrieved_contexts: [''],
  });

  useEffect(() => {
    loadProfiles();
  }, []);

  const loadProfiles = async () => {
    try {
      const profs = await profileAPI.list();
      setProfiles(profs);
      if (profs.length > 0) {
        setSingleForm((prev) => ({ ...prev, profile_id: profs[0].id }));
        setConversationalForm((prev) => ({ ...prev, profile_id: profs[0].id }));
      }
    } catch (err: any) {
      setError('Failed to load profiles');
    }
  };

  const handleSingleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);

      const response = await evaluationAPI.startSingle({
        profile_id: singleForm.profile_id,
        prompt: singleForm.prompt,
        actual_response: singleForm.actual_response,
        retrieved_contexts: singleForm.retrieved_contexts.filter((c) => c.trim()),
        expected_response: singleForm.expected_response,
      });

      setCurrentJob(response);
      navigate(`/results/${response.job_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start evaluation');
    } finally {
      setLoading(false);
    }
  };

  const handleConversationalSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);

      const response = await evaluationAPI.startConversational({
        profile_id: conversationalForm.profile_id,
        chat_history: conversationalForm.chat_history.filter((msg) => msg.content.trim()),
        prompt: conversationalForm.prompt,
        actual_response: conversationalForm.actual_response,
        retrieved_contexts: conversationalForm.retrieved_contexts.filter((c) => c.trim()),
      });

      setCurrentJob(response);
      navigate(`/results/${response.job_id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start evaluation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-4xl mx-auto">
        <Link to="/" className="text-blue-600 hover:text-blue-700 mb-4 inline-block">← Back</Link>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-6">Start Evaluation Test</h1>

        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b mb-6">
          <button
            onClick={() => setActiveTab('single')}
            className={`px-6 py-3 font-semibold transition ${
              activeTab === 'single'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Single Evaluation
          </button>
          <button
            onClick={() => setActiveTab('conversational')}
            className={`px-6 py-3 font-semibold transition ${
              activeTab === 'conversational'
                ? 'border-b-2 border-blue-600 text-blue-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Conversational Evaluation
          </button>
        </div>

        {/* Single Evaluation Form */}
        {activeTab === 'single' && (
          <form onSubmit={handleSingleSubmit} className="bg-white rounded-lg shadow-md p-6 space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Profile</label>
              <select
                value={singleForm.profile_id}
                onChange={(e) => setSingleForm({ ...singleForm, profile_id: Number(e.target.value) })}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                required
              >
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Prompt / Question</label>
              <textarea
                value={singleForm.prompt}
                onChange={(e) => setSingleForm({ ...singleForm, prompt: e.target.value })}
                rows={4}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Actual Response</label>
              <textarea
                value={singleForm.actual_response}
                onChange={(e) => setSingleForm({ ...singleForm, actual_response: e.target.value })}
                rows={4}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Retrieved Contexts</label>
              {singleForm.retrieved_contexts.map((context, idx) => (
                <div key={idx} className="mt-2">
                  <textarea
                    value={context}
                    onChange={(e) => {
                      const newContexts = [...singleForm.retrieved_contexts];
                      newContexts[idx] = e.target.value;
                      setSingleForm({ ...singleForm, retrieved_contexts: newContexts });
                    }}
                    rows={2}
                    placeholder={`Context ${idx + 1}`}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                  />
                </div>
              ))}
              <button
                type="button"
                onClick={() =>
                  setSingleForm({
                    ...singleForm,
                    retrieved_contexts: [...singleForm.retrieved_contexts, ''],
                  })
                }
                className="mt-2 text-sm text-blue-600 hover:text-blue-700"
              >
                + Add Context
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Expected Response (Optional)</label>
              <textarea
                value={singleForm.expected_response}
                onChange={(e) => setSingleForm({ ...singleForm, expected_response: e.target.value })}
                rows={3}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-md transition disabled:opacity-50"
            >
              {loading ? 'Starting...' : 'Start Evaluation'}
            </button>
          </form>
        )}

        {/* Conversational Evaluation Form */}
        {activeTab === 'conversational' && (
          <form onSubmit={handleConversationalSubmit} className="bg-white rounded-lg shadow-md p-6 space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700">Profile</label>
              <select
                value={conversationalForm.profile_id}
                onChange={(e) =>
                  setConversationalForm({ ...conversationalForm, profile_id: Number(e.target.value) })
                }
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                required
              >
                {profiles.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Chat History</label>
              {conversationalForm.chat_history.map((msg, idx) => (
                <div key={idx} className="mt-3 p-3 bg-gray-50 rounded-md">
                  <select
                    value={msg.role}
                    onChange={(e) => {
                      const newHistory = [...conversationalForm.chat_history];
                      newHistory[idx].role = e.target.value;
                      setConversationalForm({ ...conversationalForm, chat_history: newHistory });
                    }}
                    className="w-full px-2 py-1 border border-gray-300 rounded-md mb-2 text-sm"
                  >
                    <option>user</option>
                    <option>assistant</option>
                  </select>
                  <textarea
                    value={msg.content}
                    onChange={(e) => {
                      const newHistory = [...conversationalForm.chat_history];
                      newHistory[idx].content = e.target.value;
                      setConversationalForm({ ...conversationalForm, chat_history: newHistory });
                    }}
                    rows={2}
                    className="w-full px-2 py-1 border border-gray-300 rounded-md text-sm"
                  />
                </div>
              ))}
              <button
                type="button"
                onClick={() =>
                  setConversationalForm({
                    ...conversationalForm,
                    chat_history: [...conversationalForm.chat_history, { role: 'user', content: '' }],
                  })
                }
                className="mt-2 text-sm text-blue-600 hover:text-blue-700"
              >
                + Add Message
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Current Prompt</label>
              <textarea
                value={conversationalForm.prompt}
                onChange={(e) => setConversationalForm({ ...conversationalForm, prompt: e.target.value })}
                rows={3}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Current Response</label>
              <textarea
                value={conversationalForm.actual_response}
                onChange={(e) =>
                  setConversationalForm({ ...conversationalForm, actual_response: e.target.value })
                }
                rows={3}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-md transition disabled:opacity-50"
            >
              {loading ? 'Starting...' : 'Start Evaluation'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default Evaluation;

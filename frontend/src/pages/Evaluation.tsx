import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { evaluationAPI, profileAPI, modelAPI } from '../services/api';
import AppShell from '../components/AppShell';

const Evaluation: React.FC = () => {
  const navigate = useNavigate();
  const { setCurrentJob, profiles, setProfiles, modelConfigs, setModelConfigs } = useApp();
  const [activeTab, setActiveTab] = useState<'single' | 'conversational'>('single');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Single evaluation state
  const [singleForm, setSingleForm] = useState({
    evaluation_profile_id: 0,
    judge_llm_profile_id: 0,
    prompt: '',
    actual_response: '',
    retrieved_contexts: [''],
    expected_response: '',
  });

  // Conversational evaluation state
  // chat_history stored as paired turns: [{user, assistant}]
  const [conversationalForm, setConversationalForm] = useState({
    evaluation_profile_id: 0,
    judge_llm_profile_id: 0,
    chat_history: [{ user: '', assistant: '' }],
    scenario: '',
    expected_outcome: '',
    prompt: '',
    actual_response: '',
    retrieved_contexts: [''],
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [profs, models] = await Promise.all([profileAPI.list(), modelAPI.list()]);
      setProfiles(profs);
      setModelConfigs(models);
      const defaultProfileId = profs.length > 0 ? profs[0].id : 0;

      // Prefer local Ollama mistral profile as default when available.
      const preferredModel = models.find((m: { id: number; name?: string; provider: string; model_name: string }) =>
        (m.name || '').toLowerCase() === 'mistral local default' ||
        (
          (m.provider || '').toLowerCase() === 'ollama' &&
          (m.model_name || '').toLowerCase() === 'mistral'
        )
      );
      const defaultModelId = preferredModel?.id ?? (models.length > 0 ? models[0].id : 0);

      setSingleForm((prev) => ({ ...prev, evaluation_profile_id: defaultProfileId, judge_llm_profile_id: defaultModelId }));
      setConversationalForm((prev) => ({ ...prev, evaluation_profile_id: defaultProfileId, judge_llm_profile_id: defaultModelId }));
    } catch (err: any) {
      setError('Failed to load profiles or models');
    }
  };

  const handleSingleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);

      const response = await evaluationAPI.startSingle({
        evaluation_profile_id: singleForm.evaluation_profile_id,
        judge_llm_profile_id: singleForm.judge_llm_profile_id,
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
        evaluation_profile_id: conversationalForm.evaluation_profile_id,
        judge_llm_profile_id: conversationalForm.judge_llm_profile_id,
        // Flatten pairs -> [{role,content}], skip fully empty pairs
        chat_history: conversationalForm.chat_history
          .flatMap((pair) => [
            { role: 'user', content: pair.user },
            { role: 'assistant', content: pair.assistant },
          ])
          .filter((msg) => msg.content.trim()),
        scenario: conversationalForm.scenario || undefined,
        expected_outcome: conversationalForm.expected_outcome || undefined,
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
    <AppShell>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-stone-800 mb-6">Start Evaluation Test</h1>

        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* Tabs */}
        <div className="flex border-b border-stone-200 mb-6">
          <button
            onClick={() => setActiveTab('single')}
            className={`px-6 py-3 font-semibold transition ${
              activeTab === 'single'
                ? 'border-b-2 border-amber-500 text-amber-700'
                : 'text-stone-500 hover:text-stone-800'
            }`}
          >
            Single Evaluation
          </button>
          <button
            onClick={() => setActiveTab('conversational')}
            className={`px-6 py-3 font-semibold transition ${
              activeTab === 'conversational'
                ? 'border-b-2 border-amber-500 text-amber-700'
                : 'text-stone-500 hover:text-stone-800'
            }`}
          >
            Conversational Evaluation
          </button>
        </div>

        {/* Single Evaluation Form */}
        {activeTab === 'single' && (
          <form onSubmit={handleSingleSubmit} className="bg-white rounded-lg shadow-md p-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-stone-700">
                  Judge LLM Profile
                </label>
                <select
                  value={singleForm.judge_llm_profile_id}
                  onChange={(e) => setSingleForm({ ...singleForm, judge_llm_profile_id: Number(e.target.value) })}
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                  required
                >
                  {modelConfigs.length === 0 && (
                    <option value={0} disabled>No judge LLM configured</option>
                  )}
                  {modelConfigs.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name ? `${m.name} (${m.provider} / ${m.model_name})` : `${m.provider} / ${m.model_name}`}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-stone-700">
                  Evaluation Profile
                </label>
                <select
                  value={singleForm.evaluation_profile_id}
                  onChange={(e) => setSingleForm({ ...singleForm, evaluation_profile_id: Number(e.target.value) })}
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                  required
                >
                  {profiles.length === 0 && (
                    <option value={0} disabled>No evaluation profile configured</option>
                  )}
                  {profiles.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-700">Prompt / Question</label>
              <textarea
                value={singleForm.prompt}
                onChange={(e) => setSingleForm({ ...singleForm, prompt: e.target.value })}
                rows={4}
                className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-700">Actual Response</label>
              <textarea
                value={singleForm.actual_response}
                onChange={(e) => setSingleForm({ ...singleForm, actual_response: e.target.value })}
                rows={4}
                className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-700">Retrieved Contexts</label>
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
                    className="w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
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
                className="mt-2 text-sm text-amber-600 hover:text-amber-800 font-medium"
              >
                + Add Context
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-700">
                Expected Response
                <span className="text-red-500 ml-1">*</span>
              </label>
              <textarea
                value={singleForm.expected_response}
                onChange={(e) => setSingleForm({ ...singleForm, expected_response: e.target.value })}
                rows={3}
                className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-amber-500 hover:bg-amber-600 text-white font-semibold py-2 rounded-md transition disabled:opacity-50"
            >
              {loading ? 'Starting...' : 'Start Evaluation'}
            </button>
          </form>
        )}

        {/* Conversational Evaluation Form */}
        {activeTab === 'conversational' && (
          <form onSubmit={handleConversationalSubmit} className="bg-white rounded-lg shadow-md p-6 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-stone-700">
                  Judge LLM Profile
                </label>
                <select
                  value={conversationalForm.judge_llm_profile_id}
                  onChange={(e) =>
                    setConversationalForm({ ...conversationalForm, judge_llm_profile_id: Number(e.target.value) })
                  }
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                  required
                >
                  {modelConfigs.length === 0 && (
                    <option value={0} disabled>No judge LLM configured</option>
                  )}
                  {modelConfigs.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name ? `${m.name} (${m.provider} / ${m.model_name})` : `${m.provider} / ${m.model_name}`}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-stone-700">
                  Evaluation Profile
                </label>
                <select
                  value={conversationalForm.evaluation_profile_id}
                  onChange={(e) =>
                    setConversationalForm({ ...conversationalForm, evaluation_profile_id: Number(e.target.value) })
                  }
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                  required
                >
                  {profiles.length === 0 && (
                    <option value={0} disabled>No evaluation profile configured</option>
                  )}
                  {profiles.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-stone-700">
                  Scenario <span className="text-stone-400 font-normal">(optional)</span>
                </label>
                <textarea
                  value={conversationalForm.scenario}
                  onChange={(e) => setConversationalForm({ ...conversationalForm, scenario: e.target.value })}
                  rows={3}
                  placeholder="Describe the chatbot's role or purpose, e.g. 'A customer support bot for a software product'…"
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-stone-700">
                  Expected Outcome <span className="text-stone-400 font-normal">(optional)</span>
                </label>
                <textarea
                  value={conversationalForm.expected_outcome}
                  onChange={(e) => setConversationalForm({ ...conversationalForm, expected_outcome: e.target.value })}
                  rows={3}
                  placeholder="What should the conversation accomplish? e.g. 'User's issue is resolved and they feel helped'…"
                  className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-700 mb-2">Chat History</label>
              {/* Column headers */}
              <div className="grid grid-cols-2 gap-3 mb-1 px-1">
                <span className="text-xs font-semibold text-blue-600 uppercase tracking-wide">👤 User</span>
                <span className="text-xs font-semibold text-green-600 uppercase tracking-wide">🤖 Assistant</span>
              </div>
              {conversationalForm.chat_history.map((pair, idx) => {
                const isLast = idx === conversationalForm.chat_history.length - 1;
                return (
                  <div key={idx} className="relative mt-2 p-3 bg-stone-50 rounded-md border border-stone-200">
                    {isLast && conversationalForm.chat_history.length > 1 && (
                      <button
                        type="button"
                        onClick={() =>
                          setConversationalForm({
                            ...conversationalForm,
                            chat_history: conversationalForm.chat_history.slice(0, -1),
                          })
                        }
                        className="absolute top-2 right-2 text-red-400 hover:text-red-600 text-xs font-bold leading-none"
                        title="Remove this pair"
                      >
                        ✕
                      </button>
                    )}
                    <div className="grid grid-cols-2 gap-3">
                      <textarea
                        value={pair.user}
                        onChange={(e) => {
                          const next = [...conversationalForm.chat_history];
                          next[idx] = { ...next[idx], user: e.target.value };
                          setConversationalForm({ ...conversationalForm, chat_history: next });
                        }}
                        rows={2}
                        placeholder="User message…"
                        className="w-full px-2 py-1.5 border border-blue-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-400 bg-blue-50"
                      />
                      <textarea
                        value={pair.assistant}
                        onChange={(e) => {
                          const next = [...conversationalForm.chat_history];
                          next[idx] = { ...next[idx], assistant: e.target.value };
                          setConversationalForm({ ...conversationalForm, chat_history: next });
                        }}
                        rows={2}
                        placeholder="Assistant response…"
                        className="w-full px-2 py-1.5 border border-green-200 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-green-400 bg-green-50"
                      />
                    </div>
                  </div>
                );
              })}
              <button
                type="button"
                onClick={() =>
                  setConversationalForm({
                    ...conversationalForm,
                    chat_history: [...conversationalForm.chat_history, { user: '', assistant: '' }],
                  })
                }
                className="mt-2 text-sm text-amber-600 hover:text-amber-800 font-medium"
              >
                + Add Message
              </button>
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-700">Current Prompt</label>
              <textarea
                value={conversationalForm.prompt}
                onChange={(e) => setConversationalForm({ ...conversationalForm, prompt: e.target.value })}
                rows={3}
                className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-stone-700">Current Response</label>
              <textarea
                value={conversationalForm.actual_response}
                onChange={(e) =>
                  setConversationalForm({ ...conversationalForm, actual_response: e.target.value })
                }
                rows={3}
                className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-amber-500 hover:bg-amber-600 text-white font-semibold py-2 rounded-md transition disabled:opacity-50"
            >
              {loading ? 'Starting...' : 'Start Evaluation'}
            </button>
          </form>
        )}
      </div>
    </AppShell>
  );
};

export default Evaluation;

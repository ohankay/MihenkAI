import React, { useEffect, useState } from 'react';
import AppShell from '../components/AppShell';
import { modelAPI } from '../services/api';

type ModelItem = {
  id: number;
  name?: string;
  provider: string;
  model_name: string;
};

type QAItem = {
  id: string;
  question: string;
  answer: string;
  latencyMs: number;
  createdAt: string;
};

const LLMTest: React.FC = () => {
  const [models, setModels] = useState<ModelItem[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<number>(0);
  const [question, setQuestion] = useState<string>('Merhaba, nasilsin? Kisa bir cevap ver.');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<QAItem[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await modelAPI.list();
        setModels(data || []);
        if (data && data.length > 0) {
          setSelectedModelId(data[0].id);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load LLM profiles');
      }
    };

    load();
  }, []);

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedModelId || !question.trim()) {
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const result = await modelAPI.testChat(selectedModelId, question.trim());
      const item: QAItem = {
        id: `${Date.now()}-${Math.random()}`,
        question: result.prompt,
        answer: result.response,
        latencyMs: result.latency_ms,
        createdAt: new Date().toISOString(),
      };
      setHistory((prev) => [item, ...prev]);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Model test failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-bold text-stone-800 mb-6">LLM Test</h1>

        {error && (
          <div className="mb-4 p-3 rounded border border-red-300 bg-red-100 text-red-700">
            {error}
          </div>
        )}

        <form onSubmit={handleAsk} className="bg-white rounded-lg shadow-md p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-stone-700">Judge LLM Profile</label>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(Number(e.target.value))}
              className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
              required
            >
              {models.length === 0 && (
                <option value={0} disabled>No LLM profile found</option>
              )}
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name ? `${m.name} (${m.provider} / ${m.model_name})` : `${m.provider} / ${m.model_name}`}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-stone-700">Question</label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={4}
              className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
              placeholder="Bu modele bir soru yazin..."
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading || !selectedModelId}
            className="px-5 py-2 rounded-md bg-amber-500 hover:bg-amber-600 text-white font-medium disabled:opacity-60"
          >
            {loading ? 'Testing...' : 'Ask Model'}
          </button>
        </form>

        <div className="mt-6 space-y-4">
          <h2 className="text-lg font-semibold text-stone-800">Q&A History</h2>
          {history.length === 0 ? (
            <div className="bg-white border border-stone-200 rounded-lg p-4 text-stone-500">
              Henüz test yapılmadı.
            </div>
          ) : (
            history.map((item) => (
              <div key={item.id} className="bg-white border border-stone-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-xs text-stone-500">{new Date(item.createdAt).toLocaleString()}</p>
                  <span className="text-xs px-2 py-1 rounded bg-stone-100 text-stone-700">
                    {item.latencyMs} ms
                  </span>
                </div>
                <p className="text-sm font-semibold text-stone-800 mb-1">Q:</p>
                <p className="text-sm text-stone-700 whitespace-pre-wrap">{item.question}</p>
                <p className="text-sm font-semibold text-stone-800 mt-3 mb-1">A:</p>
                <p className="text-sm text-stone-700 whitespace-pre-wrap">{item.answer || '-'}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </AppShell>
  );
};

export default LLMTest;

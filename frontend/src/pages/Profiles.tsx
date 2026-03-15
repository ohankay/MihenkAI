import React, { useEffect, useState } from 'react';
import { useApp } from '../context/AppContext';
import AppShell from '../components/AppShell';
import { profileAPI, modelAPI } from '../services/api';

// ── Metric catalog ────────────────────────────────────────────────────────────
interface MetricDef {
  key: string;
  label: string;
  description: string;
  note?: string;
}

const SINGLE_METRICS: MetricDef[] = [
  {
    key: 'faithfulness',
    label: 'Faithfulness',
    description: 'Yanıtın alınan bağlamlara (retrieval context) ne kadar sadık kaldığını ölçer.',
    note: 'retrieved_contexts gerektirir',
  },
  {
    key: 'answer_relevancy',
    label: 'Answer Relevancy',
    description: 'Yanıtın soruyu/isteği ne kadar iyi karşıladığını ölçer.',
  },
  {
    key: 'contextual_precision',
    label: 'Contextual Precision',
    description: 'Alınan bağlamların ne kadarının gerçekten alakalı olduğunu sıralamayla ölçer (RAG precision).',
    note: 'retrieved_contexts + expected_response gerektirir',
  },
  {
    key: 'contextual_recall',
    label: 'Contextual Recall',
    description: 'Beklenen yanıtı desteklemek için bağlamların ne kadarının kullanıldığını ölçer.',
    note: 'retrieved_contexts + expected_response gerektirir',
  },
  {
    key: 'contextual_relevancy',
    label: 'Contextual Relevancy',
    description: 'Alınan bağlamların giriş sorusuyla ne kadar alakalı olduğunu ölçer.',
    note: 'retrieved_contexts gerektirir',
  },
  {
    key: 'hallucination',
    label: 'Hallucination',
    description: 'Yanıtın sağlanan bağlamla çelişen veya uydurma bilgi içerip içermediğini tespit eder.',
    note: 'retrieved_contexts gerektirir',
  },
  {
    key: 'bias',
    label: 'Bias',
    description: 'Yanıtın önyargılı (cinsiyet, ırk, din vb.) içerik barındırıp barındırmadığını ölçer.',
  },
  {
    key: 'toxicity',
    label: 'Toxicity',
    description: 'Yanıtın zararlı, hakaret içeren veya saldırgan dil barındırıp barındırmadığını ölçer.',
  },
];

const CONVERSATIONAL_METRICS: MetricDef[] = [
  {
    key: 'knowledge_retention',
    label: 'Knowledge Retention',
    description: 'Modelin konuşma boyunca önceki mesajlardaki bilgileri ne kadar iyi hatırladığını ölçer.',
  },
  {
    key: 'conversation_completeness',
    label: 'Conversation Completeness',
    description: 'Konuşmanın kullanıcının tüm hedef ve sorularını ne ölçüde karşıladığını değerlendirir.',
  },
  {
    key: 'conversation_relevancy',
    label: 'Conversation Relevancy',
    description: 'Konuşmadaki her LLM yanıtının mevcut kullanıcı mesajıyla ne kadar alakalı olduğunu ölçer.',
  },
];

// ── Metric weight editor ──────────────────────────────────────────────────────
interface MetricEditorProps {
  metrics: MetricDef[];
  weights: Record<string, number>;
  onChange: (w: Record<string, number>) => void;
}

const MetricEditor: React.FC<MetricEditorProps> = ({ metrics, weights, onChange }) => {
  const enabledKeys = Object.keys(weights);
  const total = enabledKeys.reduce((s, k) => s + (weights[k] || 0), 0);
  const isValid = total >= 0.99 && total <= 1.01;

  const toggle = (key: string) => {
    if (enabledKeys.includes(key)) {
      const next = { ...weights };
      delete next[key];
      onChange(next);
    } else {
      // add with equal share
      const count = enabledKeys.length + 1;
      const share = Math.round((1 / count) * 1000) / 1000;
      const next: Record<string, number> = {};
      [...enabledKeys, key].forEach((k, i) => {
        next[k] = i === count - 1
          ? Math.round((1 - share * (count - 1)) * 1000) / 1000
          : share;
      });
      onChange(next);
    }
  };

  const autoBalance = () => {
    if (enabledKeys.length === 0) return;
    const share = Math.round((1 / enabledKeys.length) * 1000) / 1000;
    const next: Record<string, number> = {};
    enabledKeys.forEach((k, i) => {
      next[k] = i === enabledKeys.length - 1
        ? Math.round((1 - share * (enabledKeys.length - 1)) * 1000) / 1000
        : share;
    });
    onChange(next);
  };

  return (
    <div className="space-y-2">
      {metrics.map((m) => {
        const isEnabled = enabledKeys.includes(m.key);
        return (
          <div
            key={m.key}
            className={`rounded-lg border p-3 transition ${
              isEnabled ? 'border-amber-300 bg-amber-50' : 'border-stone-200 bg-stone-50'
            }`}
          >
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id={`metric-${m.key}`}
                checked={isEnabled}
                onChange={() => toggle(m.key)}
                className="mt-0 w-4 h-4 accent-amber-500 cursor-pointer flex-shrink-0"
              />
              <label htmlFor={`metric-${m.key}`} className="flex-1 cursor-pointer min-w-0">
                <span className={`font-semibold text-sm ${isEnabled ? 'text-amber-800' : 'text-stone-500'}`}>
                  {m.label}
                </span>
                <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{m.description}</p>
                {m.note && (
                  <p className="text-xs text-amber-600 mt-0.5">⚠ {m.note}</p>
                )}
              </label>
              {isEnabled && (
                <div className="flex items-center gap-1 flex-shrink-0">
                  <input
                    type="number"
                    value={weights[m.key]}
                    onChange={(e) => onChange({ ...weights, [m.key]: parseFloat(e.target.value) || 0 })}
                    min="0"
                    max="1"
                    step="0.05"
                    className="w-20 px-2 py-1 border border-amber-300 rounded-md text-sm text-right focus:outline-none focus:ring-1 focus:ring-amber-400"
                  />
                  <span className="text-xs text-amber-700 font-medium w-8">
                    {Math.round((weights[m.key] || 0) * 100)}%
                  </span>
                </div>
              )}
            </div>
          </div>
        );
      })}

      <div className="flex items-center justify-between pt-2">
        <span className={`text-sm font-semibold ${isValid ? 'text-green-600' : 'text-red-500'}`}>
          Toplam: {total.toFixed(3)} &nbsp;
          {isValid ? '✓ Geçerli' : '✗ — 1.0 olmalı'}
        </span>
        <button
          type="button"
          onClick={autoBalance}
          disabled={enabledKeys.length === 0}
          className="text-xs px-3 py-1.5 bg-gray-200 hover:bg-gray-300 rounded-md transition disabled:opacity-40 font-medium"
        >
          Eşit dağıt
        </button>
      </div>
    </div>
  );
};

// ── Page ──────────────────────────────────────────────────────────────────────
const Profiles: React.FC = () => {
  const { profiles, setProfiles, addProfile, removeProfile, updateProfile, modelConfigs, setModelConfigs } = useApp();
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [modelConfigId, setModelConfigId] = useState(0);
  const [singleWeights, setSingleWeights] = useState<Record<string, number>>({
    faithfulness: 0.5,
    answer_relevancy: 0.5,
  });
  const [convWeights, setConvWeights] = useState<Record<string, number>>({
    knowledge_retention: 0.5,
    conversation_completeness: 0.5,
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [profs, models] = await Promise.all([profileAPI.list(), modelAPI.list()]);
      setProfiles(profs);
      setModelConfigs(models);
      if (models.length > 0) setModelConfigId(models[0].id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setName('');
    setDescription('');
    setModelConfigId(modelConfigs[0]?.id || 0);
    setSingleWeights({ faithfulness: 0.5, answer_relevancy: 0.5 });
    setConvWeights({ knowledge_retention: 0.5, conversation_completeness: 0.5 });
    setEditingId(null);
  };

  const openEdit = (profile: typeof profiles[0]) => {
    setEditingId(profile.id);
    setName(profile.name);
    setDescription(profile.description || '');
    setModelConfigId(profile.model_config_id);
    setSingleWeights({ ...profile.single_weights });
    setConvWeights({ ...profile.conversational_weights });
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleClone = (profile: typeof profiles[0]) => {
    setEditingId(null);
    setName(`Copy of ${profile.name}`);
    setDescription(profile.description || '');
    setModelConfigId(profile.model_config_id);
    setSingleWeights({ ...profile.single_weights });
    setConvWeights({ ...profile.conversational_weights });
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const singleKeys = Object.keys(singleWeights);
    const convKeys = Object.keys(convWeights);

    if (singleKeys.length === 0 && convKeys.length === 0) {
      setError('En az bir metrik seçmelisiniz.');
      return;
    }
    if (singleKeys.length > 0) {
      const sum = singleKeys.reduce((s, k) => s + singleWeights[k], 0);
      if (sum < 0.99 || sum > 1.01) {
        setError(`Single metrik toplam ağırlığı 1.0 olmalı (şu an: ${sum.toFixed(3)})`);
        return;
      }
    }
    if (convKeys.length > 0) {
      const sum = convKeys.reduce((s, k) => s + convWeights[k], 0);
      if (sum < 0.99 || sum > 1.01) {
        setError(`Conversational metrik toplam ağırlığı 1.0 olmalı (şu an: ${sum.toFixed(3)})`);
        return;
      }
    }

    try {
      setIsSubmitting(true);
      if (editingId !== null) {
        // UPDATE
        const updated = await profileAPI.update(editingId, {
          name,
          description,
          model_config_id: Number(modelConfigId),
          single_weights: singleWeights,
          conversational_weights: convWeights,
        });
        updateProfile(updated);
      } else {
        // CREATE
        const newProfile = await profileAPI.create({
          name,
          description,
          model_config_id: Number(modelConfigId),
          single_weights: singleWeights,
          conversational_weights: convWeights,
        });
        addProfile(newProfile);
      }
      resetForm();
      setShowForm(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create profile');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Bu profili silmek istediğinizden emin misiniz?')) {
      try {
        await profileAPI.delete(id);
        removeProfile(id);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to delete profile');
      }
    }
  };

  return (
    <AppShell>
      <div className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold text-stone-800 mb-6">Evaluation Profiles</h1>

        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded flex justify-between items-start">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-4 font-bold text-lg leading-none">×</button>
          </div>
        )}

        <button
          onClick={() => { setShowForm(!showForm); if (!showForm) resetForm(); }}
          className="mb-6 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-md transition font-medium"
        >
          {showForm ? 'Cancel' : '+ Create Profile'}
        </button>

        {showForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-xl font-semibold text-stone-800 mb-5">
              {editingId !== null ? 'Edit Evaluation Profile' : 'New Evaluation Profile'}
            </h2>
            <form onSubmit={handleSubmit} className="space-y-6">

              {/* Basic info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-1">Profile Name *</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-1">Default Judge LLM</label>
                  <select
                    value={modelConfigId}
                    onChange={(e) => setModelConfigId(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                  >
                    {modelConfigs.map((m) => (
                      <option key={m.id} value={m.id}>
                        {m.name ? `${m.name} (${m.provider} / ${m.model_name})` : `${m.provider} / ${m.model_name}`}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-stone-700 mb-1">Description</label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={2}
                  className="w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>

              {/* Single metrics */}
              <div className="border-t pt-5">
                <div className="mb-4">
                  <h3 className="text-base font-semibold text-stone-800">Single Test Metrics</h3>
                  <p className="text-xs text-gray-500 mt-1">
                    Tekil soru-cevap değerlendirmeleri (POST /evaluate/single) için metrikler ve ağırlıkları.
                    İstediğiniz metrikleri seçin, toplam 1.0 olacak şekilde ağırlık atayın.
                  </p>
                </div>
                <MetricEditor
                  metrics={SINGLE_METRICS}
                  weights={singleWeights}
                  onChange={setSingleWeights}
                />
              </div>

              {/* Conversational metrics */}
              <div className="border-t pt-5">
                <div className="mb-4">
                  <h3 className="text-base font-semibold text-stone-800">Conversational Test Metrics</h3>
                  <p className="text-xs text-gray-500 mt-1">
                    Sohbet geçmişli değerlendirmeler (POST /evaluate/conversational) için metrikler ve ağırlıkları.
                  </p>
                </div>
                <MetricEditor
                  metrics={CONVERSATIONAL_METRICS}
                  weights={convWeights}
                  onChange={setConvWeights}
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-amber-500 hover:bg-amber-600 text-white font-semibold py-2.5 rounded-md transition disabled:opacity-50"
              >
                {isSubmitting
                  ? (editingId !== null ? 'Saving…' : 'Creating…')
                  : (editingId !== null ? 'Save Changes' : 'Create Profile')}
              </button>
            </form>
          </div>
        )}

        {/* Profile cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {loading ? (
            <div className="text-center text-gray-500 col-span-2 py-8">Loading…</div>
          ) : profiles.length === 0 ? (
            <div className="text-center text-gray-500 col-span-2 py-8">Henüz profil oluşturulmadı.</div>
          ) : (
            profiles.map((profile) => (
              <div key={profile.id} className="bg-white rounded-lg shadow-md p-6 border-l-4 border-transparent hover:border-amber-400 transition-colors">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="text-lg font-semibold text-stone-900">{profile.name}</h3>
                    {profile.description && (
                      <p className="text-sm text-stone-500 mt-0.5">{profile.description}</p>
                    )}
                  </div>
                  <div className="flex gap-2 flex-shrink-0 ml-2">
                    <button
                      onClick={() => openEdit(profile)}
                      className="text-amber-600 hover:text-amber-800 text-sm font-medium"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleClone(profile)}
                      className="text-stone-500 hover:text-stone-700 text-sm font-medium"
                    >
                      Clone
                    </button>
                    <button
                      onClick={() => handleDelete(profile.id)}
                      className="text-red-500 hover:text-red-700 text-sm font-medium"
                    >
                      Delete
                    </button>
                  </div>
                </div>

                {Object.keys(profile.single_weights).length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                      Single Metrics
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.entries(profile.single_weights).map(([k, w]) => (
                        <span
                          key={k}
                          className="inline-flex items-center px-2 py-0.5 bg-amber-50 text-amber-700 rounded-full text-xs font-medium"
                        >
                          {SINGLE_METRICS.find((m) => m.key === k)?.label ?? k}
                          <span className="ml-1 text-amber-400">{Math.round((w as number) * 100)}%</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {Object.keys(profile.conversational_weights).length > 0 && (
                  <div className="mt-3">
                    <p className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-2">
                      Conversational Metrics
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.entries(profile.conversational_weights).map(([k, w]) => (
                        <span
                          key={k}
                          className="inline-flex items-center px-2 py-0.5 bg-purple-50 text-purple-700 rounded-full text-xs font-medium"
                        >
                          {CONVERSATIONAL_METRICS.find((m) => m.key === k)?.label ?? k}
                          <span className="ml-1 text-purple-400">{Math.round((w as number) * 100)}%</span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </AppShell>
  );
};

export default Profiles;

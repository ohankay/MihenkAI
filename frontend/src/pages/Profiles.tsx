import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import AppShell from '../components/AppShell';
import { profileAPI } from '../services/api';

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
    description: 'Yan\u0131t\u0131n al\u0131nan ba\u011flamlara (retrieval context) ne kadar sad\u0131k kald\u0131\u011f\u0131n\u0131 \u00f6l\u00e7er.',
    note: 'retrieved_contexts gerektirir',
  },
  {
    key: 'answer_relevancy',
    label: 'Answer Relevancy',
    description: 'Yan\u0131t\u0131n soruyu/iste\u011fi ne kadar iyi kar\u015f\u0131lad\u0131\u011f\u0131n\u0131 \u00f6l\u00e7er.',
  },
  {
    key: 'contextual_precision',
    label: 'Contextual Precision',
    description: 'Al\u0131nan ba\u011flamlar\u0131n ne kadar\u0131n\u0131n ger\u00e7ekten alakal\u0131 oldu\u011funu s\u0131ralamaylaD\u00f6l\u00e7er (RAG precision).',
    note: 'retrieved_contexts + expected_response gerektirir',
  },
  {
    key: 'contextual_recall',
    label: 'Contextual Recall',
    description: 'Beklenen yan\u0131t\u0131 desteklemek i\u00e7in ba\u011flamlar\u0131n ne kadar\u0131n\u0131n kullan\u0131ld\u0131\u011f\u0131n\u0131 \u00f6l\u00e7er.',
    note: 'retrieved_contexts + expected_response gerektirir',
  },
  {
    key: 'contextual_relevancy',
    label: 'Contextual Relevancy',
    description: 'Al\u0131nan ba\u011flamlar\u0131n giri\u015f sorusuyla ne kadar alakal\u0131 oldu\u011funu \u00f6l\u00e7er.',
    note: 'retrieved_contexts gerektirir',
  },
];

// Penalty metrics — NOT weighted; evaluated against a threshold that zeros the composite score.
const NEGATIVE_SINGLE_METRICS: MetricDef[] = [
  {
    key: 'hallucination',
    label: 'Hallucination',
    description: 'Yan\u0131t\u0131n sa\u011flanan ba\u011flamla \u00e7eli\u015fen veya uydurma bilgi i\u00e7erip i\u00e7ermedi\u011fini tespit eder.',
    note: 'retrieved_contexts gerektirir',
  },
  {
    key: 'bias',
    label: 'Bias',
    description: 'Yan\u0131t\u0131n \u00f6nyarg\u0131l\u0131 (cinsiyet, \u0131rk, din vb.) i\u00e7erik bar\u0131nd\u0131r\u0131p bar\u0131nd\u0131rmad\u0131\u011f\u0131n\u0131 \u00f6l\u00e7er.',
  },
  {
    key: 'toxicity',
    label: 'Toxicity',
    description: 'Yan\u0131t\u0131n zararl\u0131, hakaret i\u00e7eren veya sald\u0131rgan dil bar\u0131nd\u0131r\u0131p bar\u0131nd\u0131rmad\u0131\u011f\u0131n\u0131 \u00f6l\u00e7er.',
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
    description: 'Konuşmanın kullanıcının tüm hedef ve sorularını ne ölçüde karşıladığını değerlendirir. (deepeval ≥1.x gerektirir)',
    note: 'Yüklü deepeval sürümünde mevcut değil — seçilirse atlanır.',
  },
  {
    key: 'conversation_relevancy',
    label: 'Conversation Relevancy',
    description: 'Her LLM yanıtının mevcut kullanıcı mesajıyla alakasını ölçer. (deepeval ≥1.x gerektirir)',
    note: 'Yüklü deepeval sürümünde mevcut değil — seçilirse atlanır.',
  },
];

// ── Penalty metric threshold editor ──────────────────────────────────────────────
interface PenaltyMetricEditorProps {
  metrics: MetricDef[];
  thresholds: Record<string, number>; // 0–100 scale
  onChange: (t: Record<string, number>) => void;
}

const PenaltyMetricEditor: React.FC<PenaltyMetricEditorProps> = ({ metrics, thresholds, onChange }) => {
  const toggle = (key: string) => {
    if (key in thresholds) {
      const next = { ...thresholds };
      delete next[key];
      onChange(next);
    } else {
      // Always start with the default (50) — never reuse any previously cleared value
      onChange({ ...thresholds, [key]: 50 });
    }
  };

  // Controlled number input: clamp to 0–100, never allow NaN
  const handleThresholdChange = (key: string, raw: string) => {
    const val = parseFloat(raw);
    onChange({ ...thresholds, [key]: isNaN(val) ? 0 : Math.min(100, Math.max(0, val)) });
  };

  return (
    <div className="space-y-2">
      <p className="text-xs text-red-600 bg-red-50 border border-red-200 rounded p-2">
        ⚠️ <strong>Ceza metrikleri:</strong> Ağırlandırmaya dahil edilmezler.
        Etkinleştirilen her metrik için bir eşik (0–100) belirlenir.
        Test sırasında <em>herhangi biri</em> bu değere ulaşır veya geçerse bileşik skor otomatik olarak <strong>sıfırlanır</strong>.
      </p>
      {metrics.map((m) => {
        const isEnabled = m.key in thresholds;
        return (
          <div
            key={m.key}
            className={`rounded-lg border p-3 transition ${
              isEnabled ? 'border-red-300 bg-red-50' : 'border-stone-200 bg-stone-50'
            }`}
          >
            <div className="flex items-start gap-3">
              <input
                type="checkbox"
                id={`neg-metric-${m.key}`}
                checked={isEnabled}
                onChange={() => toggle(m.key)}
                className="mt-0 w-4 h-4 accent-red-500 cursor-pointer flex-shrink-0"
              />
              <label htmlFor={`neg-metric-${m.key}`} className="flex-1 cursor-pointer min-w-0">
                <span className={`font-semibold text-sm ${isEnabled ? 'text-red-800' : 'text-stone-500'}`}>
                  {m.label}
                  {!isEnabled && <span className="ml-1 text-xs font-normal text-stone-400">(devre dışı — çalıştırılmaz)</span>}
                </span>
                <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{m.description}</p>
                {m.note && <p className="text-xs text-amber-600 mt-0.5">⚠ {m.note}</p>}
              </label>
              {isEnabled && (
                <div className="flex-shrink-0 text-right">
                  <label className="text-xs text-red-600 font-medium block mb-0.5">Eşik (0–100)</label>
                  <input
                    type="number"
                    value={thresholds[m.key]}
                    onChange={(e) => handleThresholdChange(m.key, e.target.value)}
                    min="0"
                    max="100"
                    step="1"
                    className="w-20 px-2 py-1 border border-red-300 rounded-md text-sm text-right focus:outline-none focus:ring-1 focus:ring-red-400"
                  />
                  <span className="text-xs text-red-500 block mt-0.5">≥ bu değer → skor = 0</span>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ── Metric weight editor ────────────────────────────────────────────────────────
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
      // add with equal share — floor each slice, last gets remainder
      const count = enabledKeys.length + 1;
      const shareInt = Math.floor(1000 / count);
      const lastInt = 1000 - shareInt * (count - 1);
      const next: Record<string, number> = {};
      [...enabledKeys, key].forEach((k, i) => {
        next[k] = (i === count - 1 ? lastInt : shareInt) / 1000;
      });
      onChange(next);
    }
  };

  const autoBalance = () => {
    if (enabledKeys.length === 0) return;
    const n = enabledKeys.length;
    const shareInt = Math.floor(1000 / n);     // floor → her zaman aşağı yuvarlar
    const lastInt = 1000 - shareInt * (n - 1); // kalan son dilime
    const next: Record<string, number> = {};
    enabledKeys.forEach((k, i) => {
      next[k] = (i === n - 1 ? lastInt : shareInt) / 1000;
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
                    step="0.001"
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
  const navigate = useNavigate();
  const { profiles, setProfiles, addProfile, removeProfile, updateProfile } = useApp();
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [singleWeights, setSingleWeights] = useState<Record<string, number>>({
    faithfulness: 0.5,
    answer_relevancy: 0.5,
  });
  const [singleNegativeThresholds, setSingleNegativeThresholds] = useState<Record<string, number>>({});
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
      const profs = await profileAPI.list();
      setProfiles(profs);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setName('');
    setDescription('');
    setSingleWeights({ faithfulness: 0.5, answer_relevancy: 0.5 });
    setSingleNegativeThresholds({});
    setConvWeights({ knowledge_retention: 0.5, conversation_completeness: 0.5 });
    setEditingId(null);
  };

  const openEdit = (profile: typeof profiles[0]) => {
    setEditingId(profile.id);
    setName(profile.name);
    setDescription(profile.description || '');
    const negativeKeys = new Set(NEGATIVE_SINGLE_METRICS.map((m) => m.key));
    setSingleWeights(
      Object.fromEntries(Object.entries(profile.single_weights || {}).filter(([k]) => !negativeKeys.has(k)))
    );
    setSingleNegativeThresholds({ ...(profile.single_negative_thresholds || {}) });
    setConvWeights({ ...profile.conversational_weights });
    setShowForm(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleClone = (profile: typeof profiles[0]) => {
    setEditingId(null);
    setName(`Copy of ${profile.name}`);
    setDescription(profile.description || '');
    const negativeKeys = new Set(NEGATIVE_SINGLE_METRICS.map((m) => m.key));
    setSingleWeights(
      Object.fromEntries(Object.entries(profile.single_weights || {}).filter(([k]) => !negativeKeys.has(k)))
    );
    setSingleNegativeThresholds({ ...(profile.single_negative_thresholds || {}) });
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
          single_weights: singleWeights,
          single_negative_thresholds: singleNegativeThresholds,
          conversational_weights: convWeights,
        });
        updateProfile(updated);
      } else {
        // CREATE
        const newProfile = await profileAPI.create({
          name,
          description,
          single_weights: singleWeights,
          single_negative_thresholds: singleNegativeThresholds,
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
              <div className="grid grid-cols-1 gap-4">
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

              {/* Single metrics — positive (weighted) */}
              <div className="border-t pt-5">
                <div className="mb-4">
                  <h3 className="text-base font-semibold text-stone-800">Single Test Metrics</h3>
                  <p className="text-xs text-gray-500 mt-1">
                    Tekil soru-cevap değlendirmeleri (POST /evaluate/single) için metrikler ve ağırlıkları.
                    İstediğiniz metrikleri seçin, toplam 1.0 olacak şekilde ağırlık atayın.
                  </p>
                </div>
                <MetricEditor
                  metrics={SINGLE_METRICS}
                  weights={singleWeights}
                  onChange={setSingleWeights}
                />
              </div>

              {/* Single metrics — penalty (threshold-based) */}
              <div className="border-t pt-5">
                <div className="mb-4">
                  <h3 className="text-base font-semibold text-red-700">Ceza Metrikleri (Hallucination / Bias / Toxicity)</h3>
                  <p className="text-xs text-gray-500 mt-1">
                    Bu metrikler ağırlandırmaya dahil edilmez.
                    Etkinleştirilen her metrik bir eşik değeriyle izlenir;
                    test sonuçlarında herhangi biri eşiğe ülaşırsa bileşik skor otomatik olarak <strong>0</strong> yapılır.
                  </p>
                </div>
                <PenaltyMetricEditor
                  metrics={NEGATIVE_SINGLE_METRICS}
                  thresholds={singleNegativeThresholds}
                  onChange={setSingleNegativeThresholds}
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

        {/* Profile table */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <table className="min-w-full">
            <thead className="bg-stone-50 border-b border-stone-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wide w-16">ID</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wide">Profile Name</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wide">Description</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wide">Single Metrics</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-stone-500 uppercase tracking-wide">Conv. Metrics</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-stone-500 uppercase tracking-wide">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-stone-400">Loading…</td>
                </tr>
              ) : profiles.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-stone-400">Henüz profil oluşturulmadı.</td>
                </tr>
              ) : (
                profiles.map((profile) => (
                  <tr key={profile.id} className="border-b border-stone-100 hover:bg-amber-50 transition-colors">
                    <td className="px-4 py-3 text-sm text-stone-400 font-mono">#{profile.id}</td>
                    <td className="px-4 py-3 text-sm font-semibold text-stone-900">{profile.name}</td>
                    <td className="px-4 py-3 text-sm text-stone-500 max-w-xs">
                      <span className="line-clamp-2">{profile.description || <span className="italic text-stone-300">—</span>}</span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(profile.single_weights).map(([k, w]) => (
                          <span key={k} className="inline-flex items-center px-1.5 py-0.5 bg-amber-50 text-amber-700 rounded text-xs font-medium">
                            {SINGLE_METRICS.find((m) => m.key === k)?.label ?? k}
                            <span className="ml-1 text-amber-400">{Math.round((w as number) * 100)}%</span>
                          </span>
                        ))}
                        {Object.entries(profile.single_negative_thresholds || {}).map(([k, t]) => (
                          <span key={k} className="inline-flex items-center px-1.5 py-0.5 bg-red-50 text-red-700 rounded text-xs font-medium border border-red-200">
                            {NEGATIVE_SINGLE_METRICS.find((m) => m.key === k)?.label ?? k}
                            <span className="ml-1 text-red-400">≥{t as number}</span>
                          </span>
                        ))}
                        {Object.keys(profile.single_weights).length === 0 && Object.keys(profile.single_negative_thresholds || {}).length === 0 && <span className="text-xs text-stone-300 italic">—</span>}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {Object.entries(profile.conversational_weights).map(([k, w]) => (
                          <span key={k} className="inline-flex items-center px-1.5 py-0.5 bg-purple-50 text-purple-700 rounded text-xs font-medium">
                            {CONVERSATIONAL_METRICS.find((m) => m.key === k)?.label ?? k}
                            <span className="ml-1 text-purple-400">{Math.round((w as number) * 100)}%</span>
                          </span>
                        ))}
                        {Object.keys(profile.conversational_weights).length === 0 && <span className="text-xs text-stone-300 italic">—</span>}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex gap-3 justify-end">
                        <button onClick={() => openEdit(profile)} className="text-amber-600 hover:text-amber-800 text-sm font-medium">Edit</button>
                        <button onClick={() => handleClone(profile)} className="text-stone-500 hover:text-stone-700 text-sm font-medium">Clone</button>
                        <button onClick={() => navigate(`/test?profileId=${profile.id}`)} className="text-blue-600 hover:text-blue-800 text-sm font-medium">Test</button>
                        <button onClick={() => navigate(`/monitoring?profileId=${profile.id}`)} className="text-cyan-700 hover:text-cyan-900 text-sm font-medium">Monitor</button>
                        <button onClick={() => handleDelete(profile.id)} className="text-red-500 hover:text-red-700 text-sm font-medium">Delete</button>
                      </div>
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

export default Profiles;

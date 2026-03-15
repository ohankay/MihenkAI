import React from 'react';
import AppShell from '../components/AppShell';

const API_BASE = (import.meta.env.VITE_API_BASE_URL as string) || 'http://localhost:8000';

type Method = 'GET' | 'POST' | 'PUT' | 'DELETE';

interface Endpoint {
  method: Method;
  path: string;
  summary: string;
  description: string;
}

interface Group {
  tag: string;
  icon: string;
  description: string;
  endpoints: Endpoint[];
}

const METHOD_COLORS: Record<Method, string> = {
  GET:    'bg-blue-100 text-blue-700',
  POST:   'bg-green-100 text-green-700',
  PUT:    'bg-yellow-100 text-yellow-700',
  DELETE: 'bg-red-100 text-red-700',
};

const GROUPS: Group[] = [
  {
    tag: 'System',
    icon: '🖥️',
    description: 'Backend health ve konfigürasyon durumu',
    endpoints: [
      {
        method: 'GET',
        path: '/health',
        summary: 'Health Check',
        description: 'Servisin ayakta olup olmadığını kontrol eder. {"status":"ok"} döner.',
      },
      {
        method: 'GET',
        path: '/api/config',
        summary: 'Get Config',
        description: 'Backend\'in yapılandırıldığını doğrular. {"status":"configured"} döner.',
      },
      {
        method: 'GET',
        path: '/api/status',
        summary: 'Get Status',
        description: 'DB ve Redis bağlantı durumunu raporlar.',
      },
    ],
  },
  {
    tag: 'Judge LLM Profiles',
    icon: '⚙️',
    description: 'Hakem LLM yapılandırmalarını (provider, model, API key, generation parametreleri) yönetir',
    endpoints: [
      {
        method: 'GET',
        path: '/api/model-configs',
        summary: 'List Model Configs',
        description: 'Kayıtlı tüm Judge LLM profillerini listeler.',
      },
      {
        method: 'POST',
        path: '/api/model-configs',
        summary: 'Create Model Config',
        description: 'Yeni bir Judge LLM profili oluşturur. Zorunlu alanlar: name, provider (ProviderEnum), model_name.',
      },
      {
        method: 'GET',
        path: '/api/model-configs/{config_id}',
        summary: 'Get Model Config',
        description: 'ID ile tek bir Judge LLM profilini getirir.',
      },
      {
        method: 'PUT',
        path: '/api/model-configs/{config_id}',
        summary: 'Update Model Config',
        description: 'Mevcut profili kısmen günceller. Tüm alanlar opsiyoneldir.',
      },
      {
        method: 'DELETE',
        path: '/api/model-configs/{config_id}',
        summary: 'Delete Model Config',
        description: 'Judge LLM profilini siler. Bağlı Evaluation Profiles varsa hata döner.',
      },
    ],
  },
  {
    tag: 'Evaluation Profiles',
    icon: '📋',
    description: 'Hangi metrik ağırlıklarıyla ve hangi Judge LLM ile değerlendirme yapılacağını tanımlar',
    endpoints: [
      {
        method: 'GET',
        path: '/api/profiles',
        summary: 'List Profiles',
        description: 'Tüm evaluation profillerini listeler.',
      },
      {
        method: 'POST',
        path: '/api/profiles',
        summary: 'Create Profile',
        description: 'Yeni bir evaluation profili oluşturur. single_weights ve conversational_weights toplamı 1.0 olmalıdır.',
      },
      {
        method: 'GET',
        path: '/api/profiles/{profile_id}',
        summary: 'Get Profile',
        description: 'ID ile tek bir evaluation profilini getirir.',
      },
      {
        method: 'PUT',
        path: '/api/profiles/{profile_id}',
        summary: 'Update Profile',
        description: 'Mevcut profili kısmen günceller.',
      },
      {
        method: 'DELETE',
        path: '/api/profiles/{profile_id}',
        summary: 'Delete Profile',
        description: 'Evaluation profilini siler.',
      },
    ],
  },
  {
    tag: 'Evaluation',
    icon: '🧪',
    description: 'DeepEval tabanlı LLM yanıt değerlendirme işlerini başlatır ve sonuçlarını sorgular',
    endpoints: [
      {
        method: 'POST',
        path: '/api/evaluate/single',
        summary: 'Evaluate Single',
        description: 'Tek bir LLM yanıtını değerlendirir (Faithfulness + Answer Relevancy). İş kuyruğa alınır, job_id döner.',
      },
      {
        method: 'POST',
        path: '/api/evaluate/conversational',
        summary: 'Evaluate Conversational',
        description: 'Konuşma geçmişi olan bir yanıtı değerlendirir (Knowledge Retention + Conversation Completeness).',
      },
      {
        method: 'GET',
        path: '/api/evaluate/status/{job_id}',
        summary: 'Get Evaluation Status',
        description: 'İş durumunu ve tamamlanmışsa composite_score ile metrics_breakdown\'ı döner.',
      },
      {
        method: 'GET',
        path: '/api/evaluate/jobs',
        summary: 'List Evaluation Jobs',
        description: 'Son değerlendirme işlerini listeler. Opsiyonel: limit, offset query parametreleri.',
      },
    ],
  },
];

const ApiSpecs: React.FC = () => {
  return (
    <AppShell>
      <div className="max-w-5xl mx-auto">
        <div className="flex items-start justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-stone-800">API Specs</h1>
            <p className="text-stone-500 mt-1 text-sm">
              Base URL: <code className="bg-stone-100 px-1 rounded text-stone-700">{API_BASE}</code>
            </p>
          </div>
          <div className="flex gap-3 mt-1">
            <a
              href={`${API_BASE}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700 transition text-sm font-medium"
            >
              <span>📄</span> Swagger UI
            </a>
            <a
              href={`${API_BASE}/redoc`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition text-sm font-medium"
            >
              <span>📘</span> ReDoc
            </a>
            <a
              href={`${API_BASE}/openapi.json`}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-stone-600 text-white rounded-md hover:bg-stone-700 transition text-sm font-medium"
            >
              <span>⬇️</span> openapi.json
            </a>
          </div>
        </div>

        <div className="space-y-8">
          {GROUPS.map((group) => (
            <div key={group.tag} className="bg-white rounded-lg shadow-md overflow-hidden">
              {/* Group header */}
              <div className="px-6 py-4 bg-stone-50 border-b border-stone-200 flex items-center gap-3">
                <span className="text-xl">{group.icon}</span>
                <div>
                  <h2 className="text-lg font-semibold text-stone-800">{group.tag}</h2>
                  <p className="text-sm text-stone-500">{group.description}</p>
                </div>
              </div>

              {/* Endpoints */}
              <div className="divide-y divide-stone-100">
                {group.endpoints.map((ep) => (
                  <div key={`${ep.method}-${ep.path}`} className="px-6 py-4 flex items-start gap-4">
                    <span
                      className={`mt-0.5 inline-block font-mono text-xs font-bold px-2 py-1 rounded shrink-0 w-16 text-center ${METHOD_COLORS[ep.method]}`}
                    >
                      {ep.method}
                    </span>
                    <div className="min-w-0">
                      <div className="flex items-baseline gap-3 flex-wrap">
                        <code className="text-sm font-mono text-stone-800">{ep.path}</code>
                        <span className="text-xs text-stone-400 font-medium">{ep.summary}</span>
                      </div>
                      <p className="text-sm text-stone-600 mt-1">{ep.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer note */}
        <p className="text-center text-xs text-stone-400 mt-8">
          Tüm endpoint'ler <code className="bg-stone-100 px-1 rounded">{API_BASE}/docs</code> adresindeki Swagger UI üzerinden doğrudan test edilebilir.
        </p>
      </div>
    </AppShell>
  );
};

export default ApiSpecs;

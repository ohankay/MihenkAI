import React, { useEffect, useMemo, useState } from 'react';
import AppShell from '../components/AppShell';
import { modelAPI, LLMQueryLogDetail, LLMQueryLogSummary } from '../services/api';

type ModelItem = {
  id: number;
  name?: string;
  provider: string;
  model_name: string;
};

const toLocalInputValue = (value: Date) => {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}T${pad(value.getHours())}:${pad(value.getMinutes())}`;
};

const LLMMonitoring: React.FC = () => {
  const now = useMemo(() => new Date(), []);
  const oneHourAgo = useMemo(() => new Date(now.getTime() - 60 * 60 * 1000), [now]);

  const [models, setModels] = useState<ModelItem[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<number>(0);
  const [startTime, setStartTime] = useState<string>(toLocalInputValue(oneHourAgo));
  const [endTime, setEndTime] = useState<string>(toLocalInputValue(now));

  const [items, setItems] = useState<LLMQueryLogSummary[]>([]);
  const [selectedLogId, setSelectedLogId] = useState<number | null>(null);
  const [detail, setDetail] = useState<LLMQueryLogDetail | null>(null);

  const [loadingModels, setLoadingModels] = useState<boolean>(true);
  const [loadingList, setLoadingList] = useState<boolean>(false);
  const [loadingDetail, setLoadingDetail] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadModels = async () => {
      try {
        setLoadingModels(true);
        const data = await modelAPI.list();
        setModels(data || []);
        if (data && data.length > 0) {
          setSelectedModelId(data[0].id);
        }
      } catch (err: any) {
        setError(err.response?.data?.detail || 'Failed to load LLM profiles');
      } finally {
        setLoadingModels(false);
      }
    };

    loadModels();
  }, []);

  const listLogs = async () => {
    if (!selectedModelId) {
      setError('Please select an LLM profile');
      return;
    }

    const startDate = new Date(startTime);
    const endDate = new Date(endTime);
    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
      setError('Please provide valid datetime range');
      return;
    }
    if (startDate > endDate) {
      setError('Start datetime cannot be later than end datetime');
      return;
    }

    try {
      setLoadingList(true);
      setError(null);
      setDetail(null);
      setSelectedLogId(null);

      const response = await modelAPI.listQueryLogs(selectedModelId, {
        limit: 15,
        start_time: startDate.toISOString(),
        end_time: endDate.toISOString(),
      });

      setItems(response.items || []);
      if (response.items && response.items.length > 0) {
        setSelectedLogId(response.items[0].id);
      }
    } catch (err: any) {
      setItems([]);
      setError(err.response?.data?.detail || 'Failed to list query logs');
    } finally {
      setLoadingList(false);
    }
  };

  useEffect(() => {
    if (!selectedLogId || !selectedModelId) {
      return;
    }

    const loadDetail = async () => {
      try {
        setLoadingDetail(true);
        const response = await modelAPI.getQueryLogDetail(selectedModelId, selectedLogId);
        setDetail(response);
      } catch (err: any) {
        setDetail(null);
        setError(err.response?.data?.detail || 'Failed to fetch log detail');
      } finally {
        setLoadingDetail(false);
      }
    };

    loadDetail();
  }, [selectedLogId, selectedModelId]);

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-stone-800 mb-6">LLM Monitoring</h1>

        {error && (
          <div className="mb-4 p-3 rounded border border-red-300 bg-red-100 text-red-700">
            {error}
          </div>
        )}

        <div className="bg-white rounded-lg shadow-md p-5 mb-5 grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div className="md:col-span-1">
            <label className="block text-sm font-medium text-stone-700">LLM Profile</label>
            <select
              value={selectedModelId}
              onChange={(e) => setSelectedModelId(Number(e.target.value))}
              className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
              disabled={loadingModels}
            >
              {models.length === 0 && <option value={0}>No LLM profile found</option>}
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name ? `${m.name} (${m.provider} / ${m.model_name})` : `${m.provider} / ${m.model_name}`}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-stone-700">Start DateTime</label>
            <input
              type="datetime-local"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-stone-700">End DateTime</label>
            <input
              type="datetime-local"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
            />
          </div>

          <div>
            <button
              onClick={listLogs}
              disabled={loadingModels || loadingList || !selectedModelId}
              className="w-full px-4 py-2 rounded-md bg-amber-500 hover:bg-amber-600 text-white font-medium disabled:opacity-60"
            >
              {loadingList ? 'Listing...' : 'Listele'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
          <section className="xl:col-span-1 bg-white rounded-lg shadow-md border border-stone-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-stone-200">
              <p className="text-sm font-semibold text-stone-700">Son 15 Sorgu</p>
            </div>

            <div className="max-h-[70vh] overflow-y-auto">
              {items.length === 0 ? (
                <div className="p-6 text-stone-500">Kayıt bulunamadı.</div>
              ) : (
                items.map((item) => {
                  const active = selectedLogId === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => setSelectedLogId(item.id)}
                      className={`w-full text-left px-4 py-3 border-b border-stone-100 transition ${
                        active ? 'bg-amber-50' : 'hover:bg-stone-50'
                      }`}
                    >
                      <p className="text-sm font-semibold text-stone-800">Kayıt #{item.id}</p>
                      <p className="text-xs text-stone-500 mt-1">{new Date(item.created_at).toLocaleString()}</p>
                      <p className="text-xs text-stone-500 mt-1">Latency: {item.latency_ms ?? '-'} ms</p>
                      {item.error_message && (
                        <p className="text-xs text-red-600 mt-1 truncate">{item.error_message}</p>
                      )}
                    </button>
                  );
                })
              )}
            </div>
          </section>

          <section className="xl:col-span-2 bg-white rounded-lg shadow-md border border-stone-200">
            <div className="px-5 py-4 border-b border-stone-200">
              <h2 className="text-lg font-semibold text-stone-800">Kayıt Detayı</h2>
            </div>

            {loadingDetail && (
              <div className="p-6 text-stone-500">Detay yükleniyor...</div>
            )}

            {!loadingDetail && !detail && (
              <div className="p-6 text-stone-500">Soldan bir kayıt seçin.</div>
            )}

            {!loadingDetail && detail && (
              <div className="p-5 space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-xs text-stone-500">Kayıt ID</p>
                    <p className="text-stone-800">{detail.id}</p>
                  </div>
                  <div>
                    <p className="text-xs text-stone-500">Zaman</p>
                    <p className="text-stone-800">{new Date(detail.created_at).toLocaleString()}</p>
                  </div>
                  <div>
                    <p className="text-xs text-stone-500">Latency</p>
                    <p className="text-stone-800">{detail.latency_ms ?? '-'} ms</p>
                  </div>
                  <div>
                    <p className="text-xs text-stone-500">Hata</p>
                    <p className="text-stone-800">{detail.error_message || '-'}</p>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-stone-800 mb-2">Input</h3>
                  <pre className="bg-stone-900 text-stone-100 rounded-lg p-4 text-xs overflow-x-auto whitespace-pre-wrap">
                    {detail.prompt}
                  </pre>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-stone-800 mb-2">Output</h3>
                  <pre className="bg-stone-900 text-stone-100 rounded-lg p-4 text-xs overflow-x-auto whitespace-pre-wrap">
                    {detail.response || '-'}
                  </pre>
                </div>
              </div>
            )}
          </section>
        </div>
      </div>
    </AppShell>
  );
};

export default LLMMonitoring;

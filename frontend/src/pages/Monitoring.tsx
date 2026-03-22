import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import AppShell from '../components/AppShell';
import { evaluationAPI, profileAPI, EvaluationJobDetail, EvaluationJobSummary } from '../services/api';
import { useServerRequest } from '../hooks/useServerRequest';

const STATUS_STYLE: Record<string, string> = {
  COMPLETED: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  ABORTED: 'bg-stone-200 text-stone-800',
  PROCESSING: 'bg-yellow-100 text-yellow-800',
  QUEUED: 'bg-blue-100 text-blue-800',
};

const formatDate = (value?: string | null) => {
  if (!value) {
    return '-';
  }
  return new Date(value).toLocaleString();
};

const toLocalInputValue = (value: Date) => {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}T${pad(value.getHours())}:${pad(value.getMinutes())}`;
};

const Monitoring: React.FC = () => {
  const [searchParams] = useSearchParams();
  const requestedProfileId = Number(searchParams.get('profileId') || 0);

  const now = useMemo(() => new Date(), []);
  const oneHourAgo = useMemo(() => new Date(now.getTime() - 60 * 60 * 1000), [now]);

  const [profiles, setProfiles] = useState<Array<{ id: number; name: string }>>([]);
  const [selectedProfileId, setSelectedProfileId] = useState<number>(0);
  const [startTime, setStartTime] = useState<string>(toLocalInputValue(oneHourAgo));
  const [endTime, setEndTime] = useState<string>(toLocalInputValue(now));

  const [jobs, setJobs] = useState<EvaluationJobSummary[]>([]);
  const [jobsTotal, setJobsTotal] = useState<number>(0);
  const [loadingProfiles, setLoadingProfiles] = useState<boolean>(true);
  const [jobsError, setJobsError] = useState<string | null>(null);
  const [jobsNotice, setJobsNotice] = useState<string | null>(null);

  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [checkedJobIds, setCheckedJobIds] = useState<Set<string>>(new Set());
  const [detail, setDetail] = useState<EvaluationJobDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [aborting, setAborting] = useState<boolean>(false);
  const listRequest = useServerRequest();

  const isAbortable = (status?: string) => !['COMPLETED', 'FAILED', 'ABORTED'].includes(status || '');

  const selectedSummary = useMemo(
    () => jobs.find((job) => job.job_id === selectedJobId) ?? null,
    [jobs, selectedJobId]
  );

  const loadProfiles = async () => {
    try {
      setLoadingProfiles(true);
      const data = await profileAPI.list();
      const nextProfiles = data || [];
      setProfiles(nextProfiles);

      if (nextProfiles.length === 0) {
        setSelectedProfileId(0);
        return;
      }

      const hasRequested = nextProfiles.some((p: { id: number }) => p.id === requestedProfileId);
      setSelectedProfileId(hasRequested ? requestedProfileId : nextProfiles[0].id);
    } catch (error: any) {
      setJobsError(error.response?.data?.detail || 'Failed to load evaluation profiles');
    } finally {
      setLoadingProfiles(false);
    }
  };

  const listJobs = async (silent = false) => {
    if (!selectedProfileId) {
      setJobsError('Please select an evaluation profile');
      return;
    }

    const startDate = new Date(startTime);
    const endDate = new Date(endTime);

    if (Number.isNaN(startDate.getTime()) || Number.isNaN(endDate.getTime())) {
      setJobsError('Please provide valid datetime range');
      return;
    }
    if (startDate > endDate) {
      setJobsError('Start datetime cannot be later than end datetime');
      return;
    }

    try {
      const request = () => evaluationAPI.listJobs({
        limit: 100,
        offset: 0,
        profile_id: selectedProfileId,
        start_time: startDate.toISOString(),
        end_time: endDate.toISOString(),
      });
      const data = silent ? await request() : await listRequest.run(request);

      if (!data) {
        return;
      }

      const items = data.items || data.jobs || [];
      setJobs(items);
      setJobsTotal(data.total ?? items.length);
      setJobsError(null);
      setJobsNotice(null);

      setCheckedJobIds((prev) => {
        const existingIds = new Set(items.map((job) => job.job_id));
        return new Set([...prev].filter((id) => existingIds.has(id)));
      });

      if (items.length === 0) {
        setSelectedJobId(null);
        setDetail(null);
      } else if (!selectedJobId || !items.some((job) => job.job_id === selectedJobId)) {
        setSelectedJobId(items[0].job_id);
      }
    } catch (error: any) {
      setJobsError(error.response?.data?.detail || 'Failed to fetch evaluation jobs');
    }
  };

  useEffect(() => {
    if (listRequest.error) {
      setJobsError(listRequest.error);
    }
  }, [listRequest.error]);

  const fetchDetail = async (jobId: string) => {
    try {
      setDetailLoading(true);
      const data = await evaluationAPI.getJobDetail(jobId);
      setDetail(data);
    } catch (error: any) {
      setDetail(null);
      setJobsError(error.response?.data?.detail || 'Failed to fetch job detail');
    } finally {
      setDetailLoading(false);
    }
  };

  const toggleChecked = (jobId: string) => {
    setCheckedJobIds((prev) => {
      const next = new Set(prev);
      if (next.has(jobId)) {
        next.delete(jobId);
      } else {
        next.add(jobId);
      }
      return next;
    });
  };

  const abortMany = async (jobIds: string[]) => {
    if (!jobIds.length) {
      return;
    }

    try {
      setAborting(true);
      const result = await evaluationAPI.abortJobs(jobIds);
      const aborted = result.aborted_job_ids.length;
      const skipped = result.skipped_job_ids.length;
      const missing = result.not_found_job_ids.length;
      setJobsNotice(`Abort result: aborted=${aborted}, skipped=${skipped}, missing=${missing}`);
      setJobsError(null);

      setCheckedJobIds((prev) => {
        const next = new Set(prev);
        result.aborted_job_ids.forEach((id) => next.delete(id));
        return next;
      });

      await listJobs();
      if (selectedJobId && jobIds.includes(selectedJobId)) {
        await fetchDetail(selectedJobId);
      }
    } catch (error: any) {
      setJobsError(error.response?.data?.detail || 'Failed to abort selected jobs');
    } finally {
      setAborting(false);
    }
  };

  const abortSelected = async () => {
    const selectedAbortableIds = jobs
      .filter((job) => checkedJobIds.has(job.job_id) && isAbortable(job.status))
      .map((job) => job.job_id);
    await abortMany(selectedAbortableIds);
  };

  const abortCurrent = async () => {
    if (!detail || !isAbortable(detail.status)) {
      return;
    }
    await abortMany([detail.job_id]);
  };

  useEffect(() => {
    loadProfiles();
  }, [searchParams]);

  useEffect(() => {
    if (!selectedProfileId || !requestedProfileId) {
      return;
    }
    listJobs();
  }, [selectedProfileId, requestedProfileId]);

  useEffect(() => {
    if (selectedJobId) {
      fetchDetail(selectedJobId);
    }
  }, [selectedJobId]);

  useEffect(() => {
    if (!selectedJobId) {
      return;
    }

    const activeStatus = detail?.status || selectedSummary?.status;
    if (activeStatus !== 'QUEUED' && activeStatus !== 'PROCESSING') {
      return;
    }

    const detailTimer = setInterval(() => {
      fetchDetail(selectedJobId);
    }, 3000);

    const listTimer = setInterval(() => {
      listJobs(true);
    }, 15000);

    return () => {
      clearInterval(detailTimer);
      clearInterval(listTimer);
    };
  }, [selectedJobId, detail?.status, selectedSummary?.status, selectedProfileId, startTime, endTime]);

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto">
        <h1 className="text-2xl font-bold text-stone-800 mb-6">Evaluation Monitoring</h1>

        {jobsNotice && (
          <div className="bg-blue-100 border border-blue-300 text-blue-800 rounded p-3 mb-4">
            {jobsNotice}
          </div>
        )}

        {jobsError && (
          <div className="bg-red-100 border border-red-300 text-red-700 rounded p-3 mb-4">
            {jobsError}
          </div>
        )}

        <div className="bg-white rounded-lg shadow-md p-5 mb-5 grid grid-cols-1 md:grid-cols-5 gap-4 items-end">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-stone-700">Evaluation Profile</label>
            <select
              value={selectedProfileId}
              onChange={(e) => setSelectedProfileId(Number(e.target.value))}
              className="mt-1 w-full px-3 py-2 border border-stone-300 rounded-md focus:outline-none focus:ring-1 focus:ring-amber-500"
              disabled={loadingProfiles}
            >
              {profiles.length === 0 && <option value={0}>No profile found</option>}
              {profiles.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
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

          <div className="flex gap-2">
            <button
              onClick={() => listJobs()}
              disabled={loadingProfiles || listRequest.loading || !selectedProfileId}
              className="flex-1 px-4 py-2 rounded-md bg-amber-500 hover:bg-amber-600 text-white font-medium disabled:opacity-60"
            >
              {listRequest.loading ? 'Listing...' : 'List'}
            </button>
            <button
              onClick={abortSelected}
              disabled={aborting || jobs.filter((job) => checkedJobIds.has(job.job_id) && isAbortable(job.status)).length === 0}
              className="px-4 py-2 rounded-md bg-red-600 text-white hover:bg-red-500 disabled:bg-red-300 disabled:cursor-not-allowed transition"
            >
              {aborting ? 'Aborting...' : 'Abort'}
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
          <section className="xl:col-span-1 bg-white rounded-lg shadow-md border border-stone-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-stone-200">
              <p className="text-sm font-semibold text-stone-700">Filtered Jobs ({jobs.length} / total {jobsTotal})</p>
            </div>

            {listRequest.loading ? (
              <div className="p-6 text-stone-500">Loading jobs...</div>
            ) : jobs.length === 0 ? (
              <div className="p-6 text-stone-500">No evaluation job found yet.</div>
            ) : (
              <div className="max-h-[70vh] overflow-y-auto">
                {jobs.map((job) => {
                  const active = selectedJobId === job.job_id;
                  return (
                    <div
                      key={job.job_id}
                      className={`w-full text-left px-4 py-3 border-b border-stone-100 transition ${
                        active ? 'bg-amber-50' : 'hover:bg-stone-50'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex items-start gap-2 min-w-0">
                          <input
                            type="checkbox"
                            checked={checkedJobIds.has(job.job_id)}
                            onChange={() => toggleChecked(job.job_id)}
                            className="mt-0.5"
                            aria-label={`Select ${job.job_id}`}
                          />
                          <button
                            onClick={() => setSelectedJobId(job.job_id)}
                            className="text-left min-w-0"
                          >
                            <p className="font-mono text-xs text-stone-700 truncate">{job.job_id}</p>
                            <p className="text-xs text-stone-500 mt-1">
                              {job.evaluation_type} • {formatDate(job.created_at)}
                            </p>
                          </button>
                        </div>
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-semibold whitespace-nowrap ${
                            STATUS_STYLE[job.status] || 'bg-stone-100 text-stone-800'
                          }`}
                        >
                          {job.status}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          <section className="xl:col-span-2 bg-white rounded-lg shadow-md border border-stone-200">
            <div className="px-5 py-4 border-b border-stone-200">
              <h2 className="text-lg font-semibold text-stone-800">Job Detail</h2>
            </div>

            {!selectedJobId && (
              <div className="p-6 text-stone-500">Select an evaluation job to inspect details.</div>
            )}

            {selectedJobId && detailLoading && !detail && (
              <div className="p-6 text-stone-500">Loading job detail...</div>
            )}

            {selectedJobId && detail && (
              <div className="p-5 space-y-5">
                <div className="flex justify-end">
                  <button
                    onClick={abortCurrent}
                    disabled={aborting || !isAbortable(detail.status)}
                    className="px-3 py-2 rounded-md bg-red-600 text-white text-sm hover:bg-red-500 disabled:bg-red-300 disabled:cursor-not-allowed transition"
                  >
                    {aborting ? 'Aborting...' : 'Abort Job'}
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-stone-500">Job ID</p>
                    <p className="text-sm font-mono break-all text-stone-800">{detail.job_id}</p>
                  </div>
                  <div>
                    <p className="text-xs text-stone-500">Status</p>
                    <span
                      className={`inline-block mt-1 px-2 py-1 rounded-full text-xs font-semibold ${
                        STATUS_STYLE[detail.status] || 'bg-stone-100 text-stone-800'
                      }`}
                    >
                      {detail.status}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-stone-500">Type</p>
                    <p className="text-sm text-stone-800">{detail.evaluation_type}</p>
                  </div>
                  <div>
                    <p className="text-xs text-stone-500">Profile ID</p>
                    <p className="text-sm text-stone-800">{detail.profile_id}</p>
                  </div>
                  <div>
                    <p className="text-xs text-stone-500">Created</p>
                    <p className="text-sm text-stone-800">{formatDate(detail.created_at)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-stone-500">Completed</p>
                    <p className="text-sm text-stone-800">{formatDate(detail.completed_at)}</p>
                  </div>
                </div>

                {typeof detail.composite_score === 'number' && (
                  <div className="bg-stone-900 text-white rounded-lg p-4">
                    <p className="text-xs uppercase tracking-wider text-amber-400">Composite Score</p>
                    <p className="text-4xl font-bold mt-1">{detail.composite_score.toFixed(1)}</p>
                  </div>
                )}

                {detail.error_message && (
                  <div className="bg-red-50 border border-red-200 text-red-700 rounded p-3 text-sm">
                    {detail.error_message}
                  </div>
                )}

                <div>
                  <h3 className="text-sm font-semibold text-stone-800 mb-2">Request Input</h3>
                  <pre className="bg-stone-900 text-stone-100 rounded-lg p-4 text-xs overflow-x-auto">
                    {JSON.stringify(detail.request_payload || {}, null, 2)}
                  </pre>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-stone-800 mb-2">Result Output</h3>
                  <pre className="bg-stone-900 text-stone-100 rounded-lg p-4 text-xs overflow-x-auto">
                    {JSON.stringify(detail.result_payload || {}, null, 2)}
                  </pre>
                </div>

                {detail.metrics_breakdown && (
                  <div>
                    <h3 className="text-sm font-semibold text-stone-800 mb-2">Metrics Breakdown</h3>
                    <pre className="bg-stone-100 text-stone-800 rounded-lg p-4 text-xs overflow-x-auto border border-stone-200">
                      {JSON.stringify(detail.metrics_breakdown, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </section>
        </div>
      </div>
    </AppShell>
  );
};

export default Monitoring;

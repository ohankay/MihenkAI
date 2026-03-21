import React, { useEffect, useMemo, useState } from 'react';
import AppShell from '../components/AppShell';
import { evaluationAPI, EvaluationJobDetail, EvaluationJobSummary } from '../services/api';

const STATUS_STYLE: Record<string, string> = {
  COMPLETED: 'bg-green-100 text-green-800',
  FAILED: 'bg-red-100 text-red-800',
  PROCESSING: 'bg-yellow-100 text-yellow-800',
  QUEUED: 'bg-blue-100 text-blue-800',
};

const formatDate = (value?: string | null) => {
  if (!value) {
    return '-';
  }
  return new Date(value).toLocaleString();
};

const Monitoring: React.FC = () => {
  const [jobs, setJobs] = useState<EvaluationJobSummary[]>([]);
  const [jobsLoading, setJobsLoading] = useState<boolean>(true);
  const [jobsError, setJobsError] = useState<string | null>(null);
  const [jobsNotice, setJobsNotice] = useState<string | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [checkedJobIds, setCheckedJobIds] = useState<Set<string>>(new Set());
  const [detail, setDetail] = useState<EvaluationJobDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [aborting, setAborting] = useState<boolean>(false);

  const isAbortable = (status?: string) => status !== 'COMPLETED' && status !== 'FAILED';

  const selectedSummary = useMemo(
    () => jobs.find((job) => job.job_id === selectedJobId) ?? null,
    [jobs, selectedJobId]
  );

  const fetchJobs = async () => {
    try {
      const data = await evaluationAPI.listJobs(100, 0);
      setJobs(data.jobs || []);
      setJobsError(null);

      setCheckedJobIds((prev) => {
        const existingIds = new Set((data.jobs || []).map((job) => job.job_id));
        return new Set([...prev].filter((id) => existingIds.has(id)));
      });

      if (!selectedJobId && data.jobs && data.jobs.length > 0) {
        setSelectedJobId(data.jobs[0].job_id);
      }
    } catch (error: any) {
      setJobsError(error.response?.data?.detail || 'Failed to fetch evaluation jobs');
    } finally {
      setJobsLoading(false);
    }
  };

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

      await fetchJobs();
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
    fetchJobs();
    const timer = setInterval(fetchJobs, 5000);
    return () => clearInterval(timer);
  }, []);

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

    const timer = setInterval(() => {
      fetchDetail(selectedJobId);
    }, 3000);

    return () => clearInterval(timer);
  }, [selectedJobId, detail?.status, selectedSummary?.status]);

  return (
    <AppShell>
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-6 gap-3 flex-wrap">
          <h1 className="text-2xl font-bold text-stone-800">Evaluation Monitoring</h1>
          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={abortSelected}
              disabled={aborting || jobs.filter((job) => checkedJobIds.has(job.job_id) && isAbortable(job.status)).length === 0}
              className="px-4 py-2 rounded-md bg-red-600 text-white hover:bg-red-500 disabled:bg-red-300 disabled:cursor-not-allowed transition"
            >
              {aborting ? 'Aborting...' : 'Abort Selected'}
            </button>
            <button
              onClick={fetchJobs}
              className="px-4 py-2 rounded-md bg-stone-800 text-white hover:bg-stone-700 transition"
            >
              Refresh
            </button>
          </div>
        </div>

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

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-5">
          <section className="xl:col-span-1 bg-white rounded-lg shadow-md border border-stone-200 overflow-hidden">
            <div className="px-4 py-3 border-b border-stone-200">
              <p className="text-sm font-semibold text-stone-700">Evaluation Jobs ({jobs.length})</p>
            </div>

            {jobsLoading ? (
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

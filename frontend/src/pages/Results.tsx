import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { usePolling } from '../hooks/useCustom';
import { evaluationAPI } from '../services/api';
import AppShell from '../components/AppShell';

const Results: React.FC = () => {
  const navigate = useNavigate();
  const { jobId } = useParams<{ jobId: string }>();
  const [pollEnabled, setPollEnabled] = React.useState(true);

  const { data: job, loading, error } = usePolling(
    () => evaluationAPI.getStatus(jobId!),
    2000,
    pollEnabled && jobId !== undefined
  );

  // Stop polling when job is completed or failed
  useEffect(() => {
    if (job?.status === 'COMPLETED' || job?.status === 'FAILED') {
      setPollEnabled(false);
    }
  }, [job?.status]);

  return (
    <AppShell>
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-stone-800 mb-6">Evaluation Results</h1>

        {error && !job && (
          <div className="bg-red-100 border border-red-400 text-red-700 rounded p-4 mb-6">
            {error.message}
          </div>
        )}

        {!job && loading && (
          <div className="text-center py-16">
            <div className="inline-block spinner"></div>
            <p className="mt-4 text-stone-500">Loading...</p>
          </div>
        )}

        {job && (
          <div className="space-y-6">
            {/* Job Status Card */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div>
                  <dt className="text-sm font-medium text-stone-500">Job ID</dt>
                  <dd className="text-sm font-mono text-stone-800 break-all">{job.job_id}</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-stone-500">Status</dt>
                  <dd>
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                        job.status === 'COMPLETED'
                          ? 'bg-green-100 text-green-800'
                          : job.status === 'FAILED'
                          ? 'bg-red-100 text-red-800'
                          : job.status === 'PROCESSING'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {job.status}
                    </span>
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-stone-500">Time</dt>
                  <dd className="text-stone-800 text-sm">
                    {job.created_at && new Date(job.created_at).toLocaleTimeString()}
                  </dd>
                </div>
              </div>

              {job.status === 'PROCESSING' && (
                <div className="flex items-center space-x-2 text-stone-600 text-sm">
                  <div className="spinner" style={{ width: '20px', height: '20px' }}></div>
                  <span>Evaluation in progress...</span>
                </div>
              )}
            </div>

            {/* Error Message */}
            {job.error_message && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                <h2 className="text-lg font-semibold text-red-800 mb-2">Error</h2>
                <p className="text-red-700">{job.error_message}</p>
              </div>
            )}

            {/* Composite Score Card */}
            {job.status === 'COMPLETED' && job.composite_score !== null && (
              <>
                <div className="bg-gradient-to-r from-stone-800 to-stone-900 rounded-lg shadow-lg p-8 text-white border-l-4 border-amber-400">
                  <p className="text-sm font-medium text-amber-400 uppercase tracking-widest">Composite Score</p>
                  <p className="text-7xl font-bold mt-2 text-white">{job.composite_score.toFixed(1)}</p>
                  <p className="text-stone-400 text-sm mt-2">out of 100</p>
                </div>

                {/* Metrics Breakdown */}
                {job.metrics_breakdown && (
                  <div className="bg-white rounded-lg shadow-md overflow-hidden">
                    <div className="px-6 py-4 border-b border-gray-200">
                      <h2 className="text-lg font-semibold text-gray-900">Metrics Breakdown</h2>
                    </div>
                    <div className="divide-y">
                      {Object.entries(job.metrics_breakdown).map(([metricName, metricData]: any) => (
                        <div key={metricName} className="px-6 py-4">
                          <div className="flex items-center justify-between mb-2">
                            <div>
                              <p className="font-medium text-gray-900">{metricName}</p>
                              <p className="text-sm text-gray-600">
                                Weight: {(metricData.weight * 100).toFixed(1)}%
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="text-2xl font-bold text-blue-600">{metricData.score.toFixed(1)}</p>
                              <p className="text-xs text-gray-500">Contribution: {(metricData.score * metricData.weight).toFixed(1)}</p>
                            </div>
                          </div>
                          {/* Progress bar */}
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ width: `${(metricData.score / 100) * 100}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Action Buttons */}
            <div className="flex gap-4">
              <button
                onClick={() => navigate('/test')}
                className="px-6 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-md transition font-medium"
              >
                New Test
              </button>
              <button
                onClick={() => navigate('/')}
                className="px-6 py-2 bg-stone-200 text-stone-700 rounded-md hover:bg-stone-300 transition"
              >
                Back to Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
};

export default Results;

import React from 'react';
import { Link } from 'react-router-dom';
import AppShell from '../components/AppShell';

const Dashboard: React.FC = () => {
  return (
    <AppShell>
      <div className="max-w-6xl">
            <h2 className="text-2xl font-bold text-stone-800 mb-1">Welcome to MihenkAI</h2>
            <p className="text-stone-500 text-sm mb-6">Touchstone for your LLM applications — measure quality, surface issues, validate outputs.</p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {/* Card: Models */}
              <Link to="/models" className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition cursor-pointer border-l-4 border-transparent hover:border-amber-400">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-stone-800">Judge LLM Profiles</h3>
                  <span className="flex items-center justify-center w-10 h-10 rounded-lg bg-amber-50 text-xl">⚙️</span>
                </div>
                <p className="text-stone-500 text-sm">Configure judge LLMs for evaluation</p>
              </Link>

              {/* Card: Profiles */}
              <Link to="/profiles" className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition cursor-pointer border-l-4 border-transparent hover:border-amber-400">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-stone-800">Profiles</h3>
                  <span className="flex items-center justify-center w-10 h-10 rounded-lg bg-amber-50 text-xl">📋</span>
                </div>
                <p className="text-stone-500 text-sm">Create and manage evaluation tests</p>
              </Link>

              {/* Card: Test */}
              <Link to="/test" className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition cursor-pointer border-l-4 border-transparent hover:border-amber-400">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-stone-800">Evaluation Test</h3>
                  <span className="flex items-center justify-center w-10 h-10 rounded-lg bg-amber-50 text-xl">🧪</span>
                </div>
                <p className="text-stone-500 text-sm">Run evaluation and get results</p>
              </Link>

              {/* Card: LLM Test */}
              <Link to="/llm-test" className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition cursor-pointer border-l-4 border-transparent hover:border-amber-400">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-stone-800">LLM Test</h3>
                  <span className="flex items-center justify-center w-10 h-10 rounded-lg bg-amber-50 text-xl">💬</span>
                </div>
                <p className="text-stone-500 text-sm">Quickly test if configured judge models answer prompts</p>
              </Link>

              {/* Card: LLM Monitoring */}
              <Link to="/llm-monitoring" className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition cursor-pointer border-l-4 border-transparent hover:border-amber-400">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-stone-800">LLM Monitoring</h3>
                  <span className="flex items-center justify-center w-10 h-10 rounded-lg bg-amber-50 text-xl">🕒</span>
                </div>
                <p className="text-stone-500 text-sm">Inspect recent model queries with datetime filtering</p>
              </Link>

              {/* Card: API Specs */}
              <Link to="/api-specs" className="bg-white rounded-lg shadow-md p-6 hover:shadow-xl transition cursor-pointer border-l-4 border-transparent hover:border-amber-400">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-stone-800">API Specs</h3>
                  <span className="flex items-center justify-center w-10 h-10 rounded-lg bg-amber-50 text-xl">📡</span>
                </div>
                <p className="text-stone-500 text-sm">Endpoint listesi, açıklamalar ve Swagger/ReDoc linkleri</p>
              </Link>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-amber-200">
              <h3 className="text-xl font-semibold text-stone-800 mb-4">System Information</h3>
              <dl className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-stone-500">Service</dt>
                  <dd className="text-lg font-semibold text-stone-900">MihenkAI Backend</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-stone-500">Version</dt>
                  <dd className="text-lg font-semibold text-stone-900">0.1.0</dd>
                </div>
              </dl>
            </div>
      </div>
    </AppShell>
  );
};

export default Dashboard;

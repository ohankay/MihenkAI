import React from 'react';
import { Link } from 'react-router-dom';
import MihenkLogo from '../components/MihenkLogo';

const Dashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-stone-100">
      {/* Header */}
      <header className="bg-stone-900 shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4 sm:px-6 lg:px-8 flex items-center gap-4">
          <MihenkLogo size={44} />
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">MihenkAI</h1>
            <p className="text-amber-400 text-sm font-medium">DeepEval based Tester Workbench for LLM Applications</p>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-stone-900 shadow-lg min-h-[calc(100vh-76px)] border-r border-stone-700">
          <nav className="p-6 space-y-1">
            <div className="font-semibold text-amber-400 text-xs uppercase mb-5 tracking-widest px-2">Navigation</div>

            <Link to="/" className="block px-4 py-2.5 rounded-md text-stone-300 hover:bg-stone-700 hover:text-amber-400 transition font-medium">
              Dashboard
            </Link>

            <Link to="/models" className="block px-4 py-2.5 rounded-md text-stone-300 hover:bg-stone-700 hover:text-amber-400 transition font-medium">
              Judge LLM Profiles
            </Link>

            <Link to="/profiles" className="block px-4 py-2.5 rounded-md text-stone-300 hover:bg-stone-700 hover:text-amber-400 transition font-medium">
              Evaluation Profiles
            </Link>

            <Link to="/test" className="block px-4 py-2.5 rounded-md text-stone-300 hover:bg-stone-700 hover:text-amber-400 transition font-medium">
              Start Test
            </Link>

            <Link to="/api-specs" className="block px-4 py-2.5 rounded-md text-stone-300 hover:bg-stone-700 hover:text-amber-400 transition font-medium">
              API Specs
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
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
                  <h3 className="text-lg font-semibold text-stone-800">Start Test</h3>
                  <span className="flex items-center justify-center w-10 h-10 rounded-lg bg-amber-50 text-xl">🧪</span>
                </div>
                <p className="text-stone-500 text-sm">Run evaluation and get results</p>
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
        </main>
      </div>
    </div>
  );
};

export default Dashboard;

import React from 'react';
import { Link } from 'react-router-dom';

const Dashboard: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">MihenkAI</h1>
          <p className="text-gray-600">LLM Evaluation System</p>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className="w-64 bg-white shadow-lg min-h-[calc(100vh-88px)]">
          <nav className="p-6 space-y-4">
            <div className="font-semibold text-gray-700 text-sm uppercase mb-4">Menu</div>
            
            <Link to="/" className="block px-4 py-2 rounded-md text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition">
              Dashboard
            </Link>
            
            <Link to="/models" className="block px-4 py-2 rounded-md text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition">
              Model Configuration
            </Link>
            
            <Link to="/profiles" className="block px-4 py-2 rounded-md text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition">
              Evaluation Profiles
            </Link>
            
            <Link to="/test" className="block px-4 py-2 rounded-md text-gray-700 hover:bg-blue-50 hover:text-blue-600 transition">
              Start Test
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-8">
          <div className="max-w-6xl">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Welcome to MihenkAI</h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              {/* Card: Models */}
              <Link to="/models" className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition cursor-pointer">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-800">Models</h3>
                  <span className="text-2xl">⚙️</span>
                </div>
                <p className="text-gray-600 text-sm">Configure LLM models for evaluation</p>
              </Link>

              {/* Card: Profiles */}
              <Link to="/profiles" className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition cursor-pointer">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-800">Profiles</h3>
                  <span className="text-2xl">📋</span>
                </div>
                <p className="text-gray-600 text-sm">Create and manage evaluation tests</p>
              </Link>

              {/* Card: Test */}
              <Link to="/test" className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition cursor-pointer">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-gray-800">Start Test</h3>
                  <span className="text-2xl">🧪</span>
                </div>
                <p className="text-gray-600 text-sm">Run evaluation and get results</p>
              </Link>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">System Information</h3>
              <dl className="grid grid-cols-2 gap-4">
                <div>
                  <dt className="text-sm font-medium text-gray-600">Service</dt>
                  <dd className="text-lg font-semibold text-gray-900">MihenkAI Backend</dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-gray-600">Version</dt>
                  <dd className="text-lg font-semibold text-gray-900">0.1.0</dd>
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

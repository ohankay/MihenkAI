import React from 'react';
import MihenkLogo from '../components/MihenkLogo';

const Setup: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-stone-950 via-stone-900 to-stone-800 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl p-8 max-w-md w-full text-center">
        <div className="flex justify-center mb-3">
          <MihenkLogo size={56} />
        </div>
        <h1 className="text-3xl font-bold mb-1 text-stone-900">MihenkAI</h1>
        <p className="text-amber-600 text-sm font-medium mb-6">DeepEval based Tester Workbench for LLM Applications</p>

        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 font-medium mb-2">Backend'e bağlanılamıyor</p>
          <p className="text-red-600 text-sm">
            Docker container'larının çalıştığından emin olun:
          </p>
          <pre className="mt-3 text-left bg-stone-900 text-amber-400 text-xs rounded p-3">
            docker compose up -d
          </pre>
        </div>

        <p className="text-stone-400 text-xs">
          PostgreSQL ve Redis yapılandırması Docker ortamı tarafından otomatik olarak yönetilmektedir.
        </p>
      </div>
    </div>
  );
};

export default Setup;

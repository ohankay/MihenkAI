import React from 'react';

const Setup: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 to-blue-800 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
        <h1 className="text-3xl font-bold mb-2 text-gray-800">MihenkAI</h1>
        <p className="text-gray-600 mb-6">DeepEval based Tester Workbench for LLM Applications</p>

        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-700 font-medium mb-2">Backend'e bağlanılamıyor</p>
          <p className="text-red-600 text-sm">
            Docker container'larının çalıştığından emin olun:
          </p>
          <pre className="mt-3 text-left bg-gray-800 text-green-400 text-xs rounded p-3">
            docker compose up -d
          </pre>
        </div>

        <p className="text-gray-400 text-xs">
          PostgreSQL ve Redis yapılandırması Docker ortamı tarafından otomatik olarak yönetilmektedir.
        </p>
      </div>
    </div>
  );
};

export default Setup;

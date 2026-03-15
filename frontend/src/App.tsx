import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider, useApp } from './context/AppContext';
import { configAPI } from './services/api';
import Setup from './pages/Setup';
import Dashboard from './pages/Dashboard';
import Models from './pages/Models';
import Profiles from './pages/Profiles';
import Evaluation from './pages/Evaluation';
import Results from './pages/Results';

const AppRoutes: React.FC = () => {
  const { isConfigured, setConfig } = useApp();
  const [loading, setLoading] = React.useState(true);

  useEffect(() => {
    const checkConfig = async () => {
      try {
        // First check if the backend config file exists
        const config = await configAPI.getConfig();
        if (config.status === 'configured') {
          setConfig(config.config);
        } else {
          // Even without a config file, if DB is reachable (Docker env), mark as configured
          const status = await configAPI.getStatus();
          if (status.status === 'running') {
            // Backend is up with injected env vars — skip setup wizard
            setConfig({ db_host: 'db', db_port: 5432, db_user: '', db_name: '', redis_host: 'redis', redis_port: 6379 });
          }
        }
      } catch (error) {
        console.log('Not configured yet');
      } finally {
        setLoading(false);
      }
    };

    checkConfig();
  }, [setConfig]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!isConfigured) {
    return <Setup />;
  }

  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/models" element={<Models />} />
      <Route path="/profiles" element={<Profiles />} />
      <Route path="/test" element={<Evaluation />} />
      <Route path="/results/:jobId" element={<Results />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AppProvider>
  );
}

export default App;

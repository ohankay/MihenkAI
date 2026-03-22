import { useCallback, useState } from 'react';

export const useServerRequest = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async <T,>(fn: () => Promise<T>): Promise<T | null> => {
    try {
      setLoading(true);
      setError(null);
      return await fn();
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Request failed');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, setError, run };
};

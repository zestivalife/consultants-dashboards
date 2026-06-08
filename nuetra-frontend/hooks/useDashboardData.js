import { useState, useEffect } from 'react';
import { apiRequest, scoringAPI, profileAPI } from '../lib/api';
import { useAuth } from '../context/AuthContext';

export function useDashboardData() {
  const { user } = useAuth();
  const [data, setData] = useState({
    stats: null,
    scores: null,
    profile: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (user) loadDashboardData();
  }, [user]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [scores, profile] = await Promise.allSettled([
        scoringAPI.me(),
        profileAPI.me(),
      ]);

      setData({
        stats: null,
        scores: scores.status === 'fulfilled' ? scores.value : null,
        profile: profile.status === 'fulfilled' ? profile.value : null,
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, refresh: loadDashboardData };
}

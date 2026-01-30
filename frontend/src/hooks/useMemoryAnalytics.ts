import { useCallback, useState } from 'react';
import api, { apiCall } from '../services/api';

export interface MemoryStats {
  user_id: string;
  timestamp: string;
  messages: {
    total: number;
    summaries: number;
    avg_per_day_week: number;
    past_week: number;
  };
  vector_memory: {
    enabled: boolean;
    error_count: number;
    last_error: string | null;
  };
  compaction: {
    status: string;
    messages_since_last_compact: number;
    recommendation: string;
  };
}

export interface MemoryTimeline {
  [date: string]: number;
}

export interface AgentStats {
  [agent: string]: number;
}

export function useMemoryAnalytics() {
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [timeline, setTimeline] = useState<MemoryTimeline>({});
  const [agents, setAgents] = useState<AgentStats>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall('/api/v1/memory/stats', { method: 'GET' });
      setStats(data as MemoryStats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stats');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchTimeline = useCallback(async (days = 30) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall(`/api/v1/memory/timeline?days=${days}`, { method: 'GET' });
      setTimeline(data as MemoryTimeline);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch timeline');
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchAgentStats = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiCall('/api/v1/memory/agents', { method: 'GET' });
      setAgents(data as AgentStats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch agent stats');
    } finally {
      setLoading(false);
    }
  }, []);

  const exportConversations = useCallback(async (format: 'json' | 'csv' | 'markdown' = 'json') => {
    try {
      const response = await api.request({
        url: '/api/v1/memory/export',
        method: 'GET',
        params: { format },
        responseType: 'blob',
      });

      const blob = response.data as Blob;
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `conversations.${format === 'markdown' ? 'md' : format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
      throw err;
    }
  }, []);

  const exportProjectConversations = useCallback(async (projectId: string, format: 'json' | 'csv' | 'markdown' = 'json') => {
    try {
      const response = await api.request({
        url: `/api/v1/memory/export/project/${projectId}`,
        method: 'GET',
        params: { format },
        responseType: 'blob',
      });

      const blob = response.data as Blob;
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `project-${projectId}.${format === 'markdown' ? 'md' : format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed');
      throw err;
    }
  }, []);

  return {
    stats,
    timeline,
    agents,
    loading,
    error,
    fetchStats,
    fetchTimeline,
    fetchAgentStats,
    exportConversations,
    exportProjectConversations,
  };
}

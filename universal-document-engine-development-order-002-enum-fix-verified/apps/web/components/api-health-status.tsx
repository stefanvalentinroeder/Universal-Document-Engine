'use client';

import { normalizeApiBaseUrl } from '@ude/api-client';
import { getHealthTone, StatusBadge } from '@ude/ui';
import { useEffect, useState } from 'react';

type HealthStatus = 'checking' | 'online' | 'offline';

const labels: Readonly<Record<HealthStatus, string>> = {
  checking: 'Checking API',
  online: 'API healthy',
  offline: 'API unavailable',
};

export function ApiHealthStatus() {
  const [status, setStatus] = useState<HealthStatus>('checking');

  useEffect(() => {
    const controller = new AbortController();
    const apiBaseUrl = normalizeApiBaseUrl(
      process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000',
    );

    async function checkHealth() {
      try {
        const response = await fetch(`${apiBaseUrl}/health`, {
          cache: 'no-store',
          signal: controller.signal,
        });
        setStatus(response.ok ? 'online' : 'offline');
      } catch (error: unknown) {
        if (error instanceof DOMException && error.name === 'AbortError') return;
        setStatus('offline');
      }
    }

    void checkHealth();
    return () => {
      controller.abort();
    };
  }, []);

  return <StatusBadge label={labels[status]} tone={getHealthTone(status)} />;
}

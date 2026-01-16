import { useQuery } from '@tanstack/react-query';
import { apiClient } from './client';
import type { CircuitTemplate, CircuitType } from '@/types';

export const circuitKeys = {
  all: ['circuits'] as const,
  lists: () => [...circuitKeys.all, 'list'] as const,
  list: (filters: { circuit_type?: CircuitType | 'all' }) => [...circuitKeys.lists(), filters] as const,
};

async function fetchCircuits(circuitType?: CircuitType | 'all'): Promise<CircuitTemplate[]> {
  const params =
    circuitType && circuitType !== 'all'
      ? { circuit_type: circuitType }
      : {};

  const { data } = await apiClient.get('/circuits', { params });
  return data;
}

export function useCircuits(circuitType?: CircuitType | 'all') {
  return useQuery({
    queryKey: circuitKeys.list({ circuit_type: circuitType }),
    queryFn: () => fetchCircuits(circuitType),
  });
}


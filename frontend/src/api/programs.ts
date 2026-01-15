import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import type { Program, ProgramCreate, ProgramWithMicrocycle } from '@/types';

// Query keys
export const programKeys = {
  all: ['programs'] as const,
  lists: () => [...programKeys.all, 'list'] as const,
  list: (filters: { active_only?: boolean }) => [...programKeys.lists(), filters] as const,
  details: () => [...programKeys.all, 'detail'] as const,
  detail: (id: number) => [...programKeys.details(), id] as const,
};

// API functions
async function fetchPrograms(activeOnly = false): Promise<Program[]> {
  const params = activeOnly ? { active_only: true } : {};
  const { data } = await apiClient.get('/programs', { params });
  return data;
}

async function fetchProgram(id: number): Promise<ProgramWithMicrocycle> {
  const { data } = await apiClient.get(`/programs/${id}`);
  return data;
}

async function createProgram(program: ProgramCreate): Promise<Program> {
  const { data } = await apiClient.post('/programs', program);
  return data;
}

async function deleteProgram(id: number): Promise<void> {
  await apiClient.delete(`/programs/${id}`);
}

async function activateProgram(id: number): Promise<Program> {
  const { data } = await apiClient.patch(`/programs/${id}/activate`);
  return data;
}

// React Query hooks
export function usePrograms(activeOnly = false) {
  return useQuery({
    queryKey: programKeys.list({ active_only: activeOnly }),
    queryFn: () => fetchPrograms(activeOnly),
  });
}

export function useProgram(id: number) {
  return useQuery({
    queryKey: programKeys.detail(id),
    queryFn: () => fetchProgram(id),
    enabled: !!id,
  });
}

export function useCreateProgram() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: createProgram,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: programKeys.all });
    },
  });
}

export function useDeleteProgram() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: deleteProgram,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: programKeys.all });
    },
  });
}

export function useActivateProgram() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: activateProgram,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: programKeys.all });
    },
  });
}

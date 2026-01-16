import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import type { Movement, MovementPattern, MovementRule, MovementRuleCreate, MovementCreate } from '@/types';

// Query keys
export const settingsKeys = {
  all: ['settings'] as const,
  movements: () => [...settingsKeys.all, 'movements'] as const,
  movementsList: (filters: MovementsFilters) => [...settingsKeys.movements(), filters] as const,
  movement: (id: number) => [...settingsKeys.movements(), id] as const,
  movementRules: () => [...settingsKeys.all, 'movement-rules'] as const,
  movementFilters: () => [...settingsKeys.movements(), 'filters'] as const,
};

// Types
export interface MovementsFilters {
  pattern?: MovementPattern;
  equipment?: string;
  search?: string;
  limit?: number;
  offset?: number;
}

export interface MovementListResponse {
  movements: Movement[];
  total: number;
  limit: number;
  offset: number;
}

export interface MovementFiltersResponse {
  patterns: string[];
  regions: string[];
  equipment: string[];
  primary_disciplines: string[];
  types?: string[];
}

// API functions
async function fetchMovements(filters: MovementsFilters = {}): Promise<MovementListResponse> {
  const params = new URLSearchParams();
  if (filters.pattern) params.append('pattern', filters.pattern);
  if (filters.equipment) params.append('equipment', filters.equipment);
  if (filters.search) params.append('search', filters.search);
  if (filters.limit) params.append('limit', String(filters.limit));
  if (filters.offset) params.append('offset', String(filters.offset));
  
  const { data } = await apiClient.get('/settings/movements', { params });
  return data;
}

async function fetchMovement(id: number): Promise<Movement> {
  const { data } = await apiClient.get(`/settings/movements/${id}`);
  return data;
}

async function fetchMovementFilters(): Promise<MovementFiltersResponse> {
  const { data } = await apiClient.get('/settings/movements/filters');
  return data;
}

// React Query hooks
export function useMovements(filters: MovementsFilters = {}) {
  return useQuery({
    queryKey: settingsKeys.movementsList(filters),
    queryFn: () => fetchMovements(filters),
  });
}

export function useMovement(id: number) {
  return useQuery({
    queryKey: settingsKeys.movement(id),
    queryFn: () => fetchMovement(id),
    enabled: !!id,
  });
}

export function useMovementFilters() {
  return useQuery({
    queryKey: settingsKeys.movementFilters(),
    queryFn: fetchMovementFilters,
  });
}

async function createMovement(movement: MovementCreate): Promise<Movement> {
  const { data } = await apiClient.post('/settings/movements', movement);
  return data;
}

export function useCreateMovement() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: createMovement,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.movements() });
    },
  });
}

// Movement Rules (Favorites) API
async function fetchMovementRules(): Promise<MovementRule[]> {
  const { data } = await apiClient.get('/settings/movement-rules');
  return data;
}

async function createMovementRule(rule: MovementRuleCreate): Promise<MovementRule> {
  const { data } = await apiClient.post('/settings/movement-rules', rule);
  return data;
}

async function deleteMovementRule(ruleId: number): Promise<void> {
  await apiClient.delete(`/settings/movement-rules/${ruleId}`);
}

// React Query hooks for movement rules
export function useMovementRules() {
  return useQuery({
    queryKey: settingsKeys.movementRules(),
    queryFn: fetchMovementRules,
  });
}

export function useCreateMovementRule() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: createMovementRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.movementRules() });
    },
  });
}

export function useDeleteMovementRule() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: deleteMovementRule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: settingsKeys.movementRules() });
    },
  });
}

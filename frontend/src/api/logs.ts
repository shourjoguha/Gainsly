import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from './client';
import type {
  ActivityDefinition,
  ActivityInstanceCreate,
  CustomWorkoutCreate,
} from '@/types';

export const logsKeys = {
  all: ['logs'] as const,
  activities: () => [...logsKeys.all, 'activities'] as const,
  definitions: () => [...logsKeys.activities(), 'definitions'] as const,
};

// Activity Definitions
async function fetchActivityDefinitions(): Promise<ActivityDefinition[]> {
  const { data } = await apiClient.get('/activities/definitions');
  return data;
}

export function useActivityDefinitions() {
  return useQuery({
    queryKey: logsKeys.definitions(),
    queryFn: fetchActivityDefinitions,
  });
}

// Log Activity
async function logActivity(payload: ActivityInstanceCreate): Promise<{ id: number; status: string }> {
  const { data } = await apiClient.post('/activities/log', payload);
  return data;
}

export function useLogActivity() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: logActivity,
    onSuccess: () => {
      // Invalidate relevant queries if needed (e.g. activity history)
    },
  });
}

// Log Custom Workout
async function logCustomWorkout(payload: CustomWorkoutCreate): Promise<{ id: number }> {
  const { data } = await apiClient.post('/workouts/custom', payload);
  return data;
}

export function useLogCustomWorkout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: logCustomWorkout,
    onSuccess: () => {
      // Invalidate workout history/dashboard
    },
  });
}

import { apiClient } from './client'
import type {
  WorkoutLogCreate,
  WorkoutLogResponse,
  WorkoutLogListResponse,
  WorkoutLogSummary,
  SorenessLogCreate,
  SorenessLogResponse,
  RecoverySignalCreate,
  RecoverySignalResponse,
  ProgressSummaryResponse,
} from '../types/api'

/**
 * Logging API service
 * Endpoints: /logs/*
 */
export const loggingApi = {
  // ============== Workout Logs ==============

  /**
   * Create a workout log
   * POST /logs/workouts
   */
  createWorkout: async (data: WorkoutLogCreate): Promise<WorkoutLogSummary> => {
    return apiClient.post<WorkoutLogSummary>('/logs/workouts', data)
  },

  /**
   * Get workout logs
   * GET /logs/workouts
   */
  listWorkouts: async (params?: {
    limit?: number
    offset?: number
    start_date?: string
    end_date?: string
  }): Promise<WorkoutLogListResponse> => {
    return apiClient.get<WorkoutLogListResponse>('/logs/workouts', { params })
  },

  /**
   * Get a single workout log
   * GET /logs/workouts/{id}
   */
  getWorkout: async (id: number): Promise<WorkoutLogResponse> => {
    return apiClient.get<WorkoutLogResponse>(`/logs/workouts/${id}`)
  },

  // ============== Soreness Logs ==============

  /**
   * Create a soreness log
   * POST /logs/soreness
   */
  createSoreness: async (data: SorenessLogCreate): Promise<SorenessLogResponse> => {
    return apiClient.post<SorenessLogResponse>('/logs/soreness', data)
  },

  /**
   * Batch create soreness logs (multiple body parts)
   * POST /logs/soreness/batch
   */
  createSorenessBatch: async (data: SorenessLogCreate[]): Promise<SorenessLogResponse[]> => {
    return apiClient.post<SorenessLogResponse[]>('/logs/soreness/batch', data)
  },

  /**
   * Get soreness logs
   * GET /logs/soreness
   */
  listSoreness: async (params?: {
    limit?: number
    start_date?: string
    end_date?: string
  }): Promise<SorenessLogResponse[]> => {
    return apiClient.get<SorenessLogResponse[]>('/logs/soreness', { params })
  },

  // ============== Recovery Signals ==============

  /**
   * Create a recovery signal
   * POST /logs/recovery
   */
  createRecovery: async (data: RecoverySignalCreate): Promise<RecoverySignalResponse> => {
    return apiClient.post<RecoverySignalResponse>('/logs/recovery', data)
  },

  /**
   * Get recovery signals
   * GET /logs/recovery
   */
  listRecovery: async (params?: {
    limit?: number
    start_date?: string
    end_date?: string
  }): Promise<RecoverySignalResponse[]> => {
    return apiClient.get<RecoverySignalResponse[]>('/logs/recovery', { params })
  },

  /**
   * Get latest recovery signal
   * GET /logs/recovery/latest
   */
  getLatestRecovery: async (): Promise<RecoverySignalResponse | null> => {
    return apiClient.get<RecoverySignalResponse | null>('/logs/recovery/latest')
  },

  // ============== Progress & Metrics ==============

  /**
   * Get progress summary
   * GET /logs/progress
   */
  getProgressSummary: async (): Promise<ProgressSummaryResponse> => {
    return apiClient.get<ProgressSummaryResponse>('/logs/progress')
  },
}

import { apiClient } from './client'
import type {
  ProgramCreate,
  ProgramResponse,
  ProgramWithMicrocycleResponse,
  MicrocycleResponse,
  SessionResponse,
} from '../types/api'

/**
 * Programs API service
 * Endpoints: /programs/*
 */
export const programsApi = {
  /**
   * Create a new program
   * POST /programs
   */
  create: async (data: ProgramCreate): Promise<ProgramResponse> => {
    return apiClient.post<ProgramResponse>('/programs', data)
  },

  /**
   * Get all programs for the current user
   * GET /programs
   */
  list: async (params?: { active_only?: boolean }): Promise<ProgramResponse[]> => {
    return apiClient.get<ProgramResponse[]>('/programs', { params })
  },

  /**
   * Get a single program by ID
   * GET /programs/{id}
   */
  get: async (id: number): Promise<ProgramWithMicrocycleResponse> => {
    return apiClient.get<ProgramWithMicrocycleResponse>(`/programs/${id}`)
  },

  /**
   * Update a program
   * PUT /programs/{id}
   */
  update: async (id: number, data: Partial<ProgramCreate>): Promise<ProgramResponse> => {
    return apiClient.put<ProgramResponse>(`/programs/${id}`, data)
  },

  /**
   * Delete a program
   * DELETE /programs/{id}
   */
  delete: async (id: number): Promise<{ success: boolean }> => {
    return apiClient.delete<{ success: boolean }>(`/programs/${id}`)
  },

  /**
   * Generate the next microcycle for a program
   * POST /programs/{id}/microcycles/generate-next
   */
  generateNextMicrocycle: async (programId: number): Promise<MicrocycleResponse> => {
    return apiClient.post<MicrocycleResponse>(`/programs/${programId}/microcycles/generate-next`)
  },

  /**
   * Get all microcycles for a program
   * GET /programs/{id}/microcycles
   */
  getMicrocycles: async (programId: number): Promise<MicrocycleResponse[]> => {
    return apiClient.get<MicrocycleResponse[]>(`/programs/${programId}/microcycles`)
  },

  /**
   * Get sessions for a microcycle
   * GET /programs/{program_id}/microcycles/{microcycle_id}/sessions
   */
  getSessions: async (programId: number, microcycleId: number): Promise<SessionResponse[]> => {
    return apiClient.get<SessionResponse[]>(
      `/programs/${programId}/microcycles/${microcycleId}/sessions`
    )
  },
}

import { apiClient } from './client'
import type {
  UserSettingsUpdate,
  UserSettingsResponse,
  UserProfileUpdate,
  UserProfileResponse,
  MovementResponse,
  MovementListResponse,
  MovementRuleResponse,
  MovementRuleCreate,
  MovementRuleUpdate,
  EnjoyableActivityResponse,
  EnjoyableActivityCreate,
  EnjoyableActivityUpdate,
  HeuristicConfigListResponse,
} from '../types/api'

/**
 * Settings API service
 * Endpoints: /settings/*
 */
export const settingsApi = {
  // ============== User Settings ==============

  /**
   * Get user settings
   * GET /settings
   */
  getSettings: async (): Promise<UserSettingsResponse> => {
    return apiClient.get<UserSettingsResponse>('/settings')
  },

  /**
   * Update user settings
   * PUT /settings
   */
  updateSettings: async (data: UserSettingsUpdate): Promise<UserSettingsResponse> => {
    return apiClient.put<UserSettingsResponse>('/settings', data)
  },

  // ============== User Profile ==============

  /**
   * Get user profile
   * GET /settings/profile
   */
  getProfile: async (): Promise<UserProfileResponse> => {
    return apiClient.get<UserProfileResponse>('/settings/profile')
  },

  /**
   * Update user profile
   * PUT /settings/profile
   */
  updateProfile: async (data: UserProfileUpdate): Promise<UserProfileResponse> => {
    return apiClient.put<UserProfileResponse>('/settings/profile', data)
  },

  // ============== Movements ==============

  /**
   * List movements (repository)
   * GET /settings/movements
   */
  listMovements: async (params?: {
    pattern?: string
    region?: string
    search?: string
    limit?: number
    offset?: number
  }): Promise<MovementListResponse> => {
    return apiClient.get<MovementListResponse>('/settings/movements', { params })
  },

  /**
   * Get a single movement
   * GET /settings/movements/{id}
   */
  getMovement: async (id: number): Promise<MovementResponse> => {
    return apiClient.get<MovementResponse>(`/settings/movements/${id}`)
  },

  // ============== Movement Rules ==============

  /**
   * Get all movement rules for the user
   * GET /settings/movement-rules
   */
  listMovementRules: async (): Promise<MovementRuleResponse[]> => {
    return apiClient.get<MovementRuleResponse[]>('/settings/movement-rules')
  },

  /**
   * Create a movement rule
   * POST /settings/movement-rules
   */
  createMovementRule: async (data: MovementRuleCreate): Promise<MovementRuleResponse> => {
    return apiClient.post<MovementRuleResponse>('/settings/movement-rules', data)
  },

  /**
   * Update a movement rule
   * PUT /settings/movement-rules/{id}
   */
  updateMovementRule: async (id: number, data: MovementRuleUpdate): Promise<MovementRuleResponse> => {
    return apiClient.put<MovementRuleResponse>(`/settings/movement-rules/${id}`, data)
  },

  /**
   * Delete a movement rule
   * DELETE /settings/movement-rules/{id}
   */
  deleteMovementRule: async (id: number): Promise<{ success: boolean }> => {
    return apiClient.delete<{ success: boolean }>(`/settings/movement-rules/${id}`)
  },

  // ============== Enjoyable Activities ==============

  /**
   * Get all enjoyable activities for the user
   * GET /settings/enjoyable-activities
   */
  listEnjoyableActivities: async (): Promise<EnjoyableActivityResponse[]> => {
    return apiClient.get<EnjoyableActivityResponse[]>('/settings/enjoyable-activities')
  },

  /**
   * Create an enjoyable activity
   * POST /settings/enjoyable-activities
   */
  createEnjoyableActivity: async (data: EnjoyableActivityCreate): Promise<EnjoyableActivityResponse> => {
    return apiClient.post<EnjoyableActivityResponse>('/settings/enjoyable-activities', data)
  },

  /**
   * Update an enjoyable activity
   * PUT /settings/enjoyable-activities/{id}
   */
  updateEnjoyableActivity: async (id: number, data: EnjoyableActivityUpdate): Promise<EnjoyableActivityResponse> => {
    return apiClient.put<EnjoyableActivityResponse>(`/settings/enjoyable-activities/${id}`, data)
  },

  /**
   * Delete an enjoyable activity
   * DELETE /settings/enjoyable-activities/{id}
   */
  deleteEnjoyableActivity: async (id: number): Promise<{ success: boolean }> => {
    return apiClient.delete<{ success: boolean }>(`/settings/enjoyable-activities/${id}`)
  },

  // ============== Heuristics (Read-Only) ==============

  /**
   * Get all heuristic configurations
   * GET /settings/heuristics
   */
  listHeuristics: async (): Promise<HeuristicConfigListResponse> => {
    return apiClient.get<HeuristicConfigListResponse>('/settings/heuristics')
  },
}

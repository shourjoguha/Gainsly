import { apiClient } from './client'
import type { SSEMessageEvent, ApiError } from './client'
import type {
  DailyPlanResponse,
  AdaptationRequest,
  AdaptationResponse,
  AcceptPlanRequest,
  AcceptPlanResponse,
} from '../types/api'

/**
 * Daily planning API service
 * Endpoints: /days/*
 */
export const dailyApi = {
  /**
   * Get the daily plan for a specific date
   * GET /days/{date}/plan?program_id={program_id}
   */
  getPlan: async (date: string, programId: number): Promise<DailyPlanResponse> => {
    return apiClient.get<DailyPlanResponse>(`/days/${date}/plan`, {
      params: { program_id: programId },
    })
  },

  /**
   * Adapt a session (non-streaming)
   * POST /days/{date}/adapt
   */
  adaptSession: async (date: string, data: AdaptationRequest): Promise<AdaptationResponse> => {
    return apiClient.post<AdaptationResponse>(`/days/${date}/adapt`, data)
  },

  /**
   * Adapt a session with SSE streaming
   * POST /days/{date}/adapt/stream
   * @param date - Target date in YYYY-MM-DD format
   * @param data - Adaptation request data
   * @param onMessage - Callback for SSE messages
   * @param onError - Callback for errors
   */
  adaptSessionStream: async (
    date: string,
    data: AdaptationRequest,
    onMessage?: (event: SSEMessageEvent) => void,
    onError?: (error: ApiError) => void
  ): Promise<void> => {
    return apiClient.streamSSE(`/days/${date}/adapt/stream`, data, onMessage, onError)
  },

  /**
   * Accept an adapted plan from a conversation
   * POST /days/accept-plan
   */
  acceptPlan: async (data: AcceptPlanRequest): Promise<AcceptPlanResponse> => {
    return apiClient.post<AcceptPlanResponse>('/days/accept-plan', data)
  },
}

/**
 * Helper function to format date for API
 */
export function formatDateForApi(date: Date): string {
  return date.toISOString().split('T')[0]
}

/**
 * Get today's date formatted for API
 */
export function getTodayForApi(): string {
  return formatDateForApi(new Date())
}

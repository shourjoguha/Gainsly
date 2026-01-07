import { API_BASE_URL } from '../utils/constants'

export interface FetchOptions extends Omit<RequestInit, 'body'> {
  params?: Record<string, string | number | boolean>
  body?: any
  retry?: boolean
  maxRetries?: number
}

export interface ApiError {
  status: number
  message: string
  data?: any
  retryable?: boolean
}

// HTTP status codes that are retryable
const RETRYABLE_STATUS_CODES = [408, 429, 500, 502, 503, 504]
const DEFAULT_MAX_RETRIES = 3
const BASE_DELAY_MS = 1000

/**
 * Calculate delay with exponential backoff and jitter
 */
function getRetryDelay(attempt: number): number {
  const exponentialDelay = BASE_DELAY_MS * Math.pow(2, attempt)
  const jitter = Math.random() * 200 // Add 0-200ms jitter
  return Math.min(exponentialDelay + jitter, 10000) // Cap at 10s
}

/**
 * Check if an error is retryable
 */
function isRetryable(error: ApiError): boolean {
  return RETRYABLE_STATUS_CODES.includes(error.status) || error.status === 0
}

/**
 * Sleep for a given duration
 */
function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

class ApiClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  private buildUrl(endpoint: string, params?: Record<string, any>): string {
    const url = new URL(`${this.baseUrl}${endpoint}`)

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, String(value))
        }
      })
    }

    return url.toString()
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    // Check if response is JSON
    const contentType = response.headers.get('content-type')
    const isJson = contentType?.includes('application/json')

    let data: any
    if (isJson) {
      data = await response.json()
    } else {
      data = await response.text()
    }

    if (!response.ok) {
      let errorMessage = response.statusText

      // Handle FastAPI/Pydantic validation errors (array of errors)
      if (Array.isArray(data?.detail)) {
        errorMessage = data.detail
          .map((e: any) => e.msg || JSON.stringify(e))
          .join('; ')
      }
      // Handle simple error message
      else if (typeof data?.detail === 'string') {
        errorMessage = data.detail
      }
      else if (data?.message) {
        errorMessage = data.message
      }

      const error: ApiError = {
        status: response.status,
        message: errorMessage,
        data,
      }
      throw error
    }

    return data as T
  }

  /**
   * Execute a fetch with automatic retry on failure
   */
  private async fetchWithRetry(
    url: string,
    fetchOptions: RequestInit,
    options?: FetchOptions
  ): Promise<Response> {
    const maxRetries = options?.retry === false ? 0 : (options?.maxRetries ?? DEFAULT_MAX_RETRIES)
    let lastError: ApiError | null = null

    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const response = await fetch(url, fetchOptions)

        if (!response.ok) {
          const contentType = response.headers.get('content-type')
          const isJson = contentType?.includes('application/json')
          let data: any
          try {
            data = isJson ? await response.json() : await response.text()
          } catch {
            data = null
          }

          let errorMessage = response.statusText
          if (Array.isArray(data?.detail)) {
            errorMessage = data.detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ')
          } else if (typeof data?.detail === 'string') {
            errorMessage = data.detail
          } else if (data?.message) {
            errorMessage = data.message
          }

          const error: ApiError = {
            status: response.status,
            message: errorMessage,
            data,
            retryable: isRetryable({ status: response.status, message: '' }),
          }

          // Don't retry non-retryable errors
          if (!isRetryable(error) || attempt === maxRetries) {
            throw error
          }

          lastError = error
          const delay = getRetryDelay(attempt)
          console.warn(`Request failed with status ${response.status}, retrying in ${delay}ms (attempt ${attempt + 1}/${maxRetries})`)
          await sleep(delay)
          continue
        }

        return response
      } catch (err: any) {
        // Network errors (fetch throws)
        if (err.status === undefined) {
          const networkError: ApiError = {
            status: 0,
            message: err.message || 'Network error',
            retryable: true,
          }

          if (attempt === maxRetries) {
            throw networkError
          }

          lastError = networkError
          const delay = getRetryDelay(attempt)
          console.warn(`Network error, retrying in ${delay}ms (attempt ${attempt + 1}/${maxRetries})`)
          await sleep(delay)
          continue
        }

        // Re-throw API errors
        throw err
      }
    }

    throw lastError || new Error('Request failed after retries')
  }

  async get<T>(endpoint: string, options?: FetchOptions): Promise<T> {
    const url = this.buildUrl(endpoint, options?.params)
    const response = await this.fetchWithRetry(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    }, options)

    return this.handleResponse<T>(response)
  }

  async post<T>(endpoint: string, data?: any, options?: FetchOptions): Promise<T> {
    const url = this.buildUrl(endpoint, options?.params)
    const response = await this.fetchWithRetry(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    }, options)

    return this.handleResponse<T>(response)
  }

  async put<T>(endpoint: string, data?: any, options?: FetchOptions): Promise<T> {
    const url = this.buildUrl(endpoint, options?.params)
    const response = await this.fetchWithRetry(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    }, options)

    return this.handleResponse<T>(response)
  }

  async delete<T>(endpoint: string, options?: FetchOptions): Promise<T> {
    const url = this.buildUrl(endpoint, options?.params)
    const response = await this.fetchWithRetry(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    }, options)

    return this.handleResponse<T>(response)
  }

  /**
   * Stream a Server-Sent Events (SSE) response
   * @param endpoint API endpoint
   * @param data Request body data
   * @param onMessage Callback for each message chunk
   * @param onError Callback for errors
   */
  async streamSSE(
    endpoint: string,
    data?: any,
    onMessage?: (event: SSEMessageEvent) => void,
    onError?: (error: ApiError) => void
  ): Promise<void> {
    const url = this.buildUrl(endpoint)

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        const errorData = await response.json()
        const error: ApiError = {
          status: response.status,
          message: errorData?.detail || response.statusText,
          data: errorData,
        }
        onError?.(error)
        throw error
      }

      // Parse SSE stream
      const reader = response.body?.getReader()
      if (!reader) {
        throw new Error('Response body is not readable')
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')

        // Keep last incomplete line in buffer
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            if (dataStr === '[DONE]') {
              onMessage?.({ type: 'done', data: null })
              continue
            }

            try {
              const parsed = JSON.parse(dataStr)
              if (parsed.error) {
                onMessage?.({ type: 'error', data: parsed.error })
              } else if (parsed.content) {
                onMessage?.({ type: 'content', data: parsed.content, done: parsed.done })
              } else if (parsed.recovery_score !== undefined) {
                onMessage?.({ type: 'recovery_score', data: parsed.recovery_score })
              } else if (parsed.thread_id) {
                onMessage?.({ type: 'thread_id', data: parsed.thread_id })
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', dataStr)
            }
          }
        }
      }

      // Handle any remaining buffer
      if (buffer && buffer.startsWith('data: ')) {
        const dataStr = buffer.slice(6)
        try {
          const parsed = JSON.parse(dataStr)
          if (parsed.content) {
            onMessage?.({ type: 'content', data: parsed.content, done: true })
          }
        } catch (e) {
          console.error('Failed to parse final SSE data:', dataStr)
        }
      }
    } catch (error) {
      const apiError: ApiError = {
        status: 0,
        message: error instanceof Error ? error.message : 'Unknown error',
      }
      onError?.(apiError)
    }
  }
}

export interface SSEMessageEvent {
  type: 'recovery_score' | 'thread_id' | 'content' | 'error' | 'done'
  data: any
  done?: boolean
}

export const apiClient = new ApiClient()

import { API_BASE_URL } from '../utils/constants'

export interface FetchOptions extends Omit<RequestInit, 'body'> {
  params?: Record<string, string | number | boolean>
  body?: any
}

export interface ApiError {
  status: number
  message: string
  data?: any
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
      const error: ApiError = {
        status: response.status,
        message: data?.detail || data?.message || response.statusText,
        data,
      }
      throw error
    }

    return data as T
  }

  async get<T>(endpoint: string, options?: FetchOptions): Promise<T> {
    const url = this.buildUrl(endpoint, options?.params)
    const response = await fetch(url, {
      method: 'GET',
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    return this.handleResponse<T>(response)
  }

  async post<T>(endpoint: string, data?: any, options?: FetchOptions): Promise<T> {
    const url = this.buildUrl(endpoint, options?.params)
    const response = await fetch(url, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    return this.handleResponse<T>(response)
  }

  async put<T>(endpoint: string, data?: any, options?: FetchOptions): Promise<T> {
    const url = this.buildUrl(endpoint, options?.params)
    const response = await fetch(url, {
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

    return this.handleResponse<T>(response)
  }

  async delete<T>(endpoint: string, options?: FetchOptions): Promise<T> {
    const url = this.buildUrl(endpoint, options?.params)
    const response = await fetch(url, {
      method: 'DELETE',
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    })

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

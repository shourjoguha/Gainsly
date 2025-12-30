import { useState, useCallback, useRef } from 'react'
import { apiClient } from '../api/client'
import type { SSEMessageEvent, ApiError } from '../api/client'

interface UseSseOptions<T> {
  onMessage?: (event: SSEMessageEvent) => void
  onError?: (error: ApiError) => void
  onComplete?: (data: T) => void
}

interface UseSseReturn<T> {
  data: T | null
  content: string
  recoveryScore: number | null
  threadId: number | null
  isStreaming: boolean
  error: ApiError | null
  start: (endpoint: string, requestData?: any) => Promise<void>
  reset: () => void
}

/**
 * Hook for handling Server-Sent Events streaming
 * Specifically designed for the session adaptation streaming endpoint
 */
function useSse<T = any>(options: UseSseOptions<T> = {}): UseSseReturn<T> {
  const [data, setData] = useState<T | null>(null)
  const [content, setContent] = useState('')
  const [recoveryScore, setRecoveryScore] = useState<number | null>(null)
  const [threadId, setThreadId] = useState<number | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  const contentRef = useRef('')
  const abortControllerRef = useRef<AbortController | null>(null)

  const handleMessage = useCallback(
    (event: SSEMessageEvent) => {
      options.onMessage?.(event)

      switch (event.type) {
        case 'recovery_score':
          setRecoveryScore(event.data)
          break
        case 'thread_id':
          setThreadId(event.data)
          break
        case 'content':
          contentRef.current += event.data
          setContent(contentRef.current)
          if (event.done) {
            setIsStreaming(false)
            // Try to parse final content as JSON if possible
            try {
              const parsed = JSON.parse(contentRef.current) as T
              setData(parsed)
              options.onComplete?.(parsed)
            } catch {
              // Content is not JSON, keep as string
            }
          }
          break
        case 'error':
          const apiError: ApiError = {
            status: 0,
            message: event.data,
          }
          setError(apiError)
          setIsStreaming(false)
          options.onError?.(apiError)
          break
        case 'done':
          setIsStreaming(false)
          break
      }
    },
    [options]
  )

  const handleError = useCallback(
    (err: ApiError) => {
      setError(err)
      setIsStreaming(false)
      options.onError?.(err)
    },
    [options]
  )

  const start = useCallback(
    async (endpoint: string, requestData?: any) => {
      // Cancel any existing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }

      // Reset state
      setData(null)
      setContent('')
      contentRef.current = ''
      setRecoveryScore(null)
      setThreadId(null)
      setError(null)
      setIsStreaming(true)

      // Create new abort controller
      abortControllerRef.current = new AbortController()

      try {
        await apiClient.streamSSE(endpoint, requestData, handleMessage, handleError)
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          // Stream was cancelled
          setIsStreaming(false)
        } else {
          const apiError: ApiError = {
            status: 0,
            message: err instanceof Error ? err.message : 'Unknown error',
          }
          setError(apiError)
          setIsStreaming(false)
        }
      }
    },
    [handleMessage, handleError]
  )

  const reset = useCallback(() => {
    // Cancel any existing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    setData(null)
    setContent('')
    contentRef.current = ''
    setRecoveryScore(null)
    setThreadId(null)
    setError(null)
    setIsStreaming(false)
  }, [])

  return {
    data,
    content,
    recoveryScore,
    threadId,
    isStreaming,
    error,
    start,
    reset,
  }
}

export default useSse

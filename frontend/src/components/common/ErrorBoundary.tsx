import { Component, type ErrorInfo, type ReactNode } from 'react'
import Button from './Button'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface State {
  hasError: boolean
  error: Error | null
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo)
    this.props.onError?.(error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  private handleReload = () => {
    window.location.reload()
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="min-h-[400px] flex items-center justify-center p-8">
          <div className="max-w-md text-center">
            <div className="w-16 h-16 mx-auto mb-4 bg-destructive-100 rounded-full flex items-center justify-center">
              <ExclamationTriangleIcon className="w-8 h-8 text-destructive-600" />
            </div>
            <h2 className="text-xl font-semibold text-secondary-900 mb-2">
              Something went wrong
            </h2>
            <p className="text-secondary-600 mb-6">
              We encountered an unexpected error. Please try again.
            </p>
            {this.state.error && (
              <details className="mb-6 text-left bg-secondary-50 rounded-lg p-4">
                <summary className="text-sm font-medium text-secondary-700 cursor-pointer">
                  Error details
                </summary>
                <pre className="mt-2 text-xs text-secondary-600 overflow-x-auto">
                  {this.state.error.message}
                </pre>
              </details>
            )}
            <div className="flex gap-3 justify-center">
              <Button variant="secondary" onClick={this.handleReset}>
                Try Again
              </Button>
              <Button onClick={this.handleReload}>
                Reload Page
              </Button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary

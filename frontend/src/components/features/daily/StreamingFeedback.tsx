import React from 'react'
import { clsx } from 'clsx'
import { Spinner } from '../../common'

interface StreamingFeedbackProps {
  content: string
  recoveryScore: number | null
  isStreaming: boolean
  error?: string | null
}

const RecoveryGauge: React.FC<{ score: number }> = ({ score }) => {
  const getColor = () => {
    if (score >= 70) return 'bg-success-500'
    if (score >= 40) return 'bg-accent-500'
    return 'bg-destructive-500'
  }

  const getLabel = () => {
    if (score >= 70) return 'Good Recovery'
    if (score >= 40) return 'Moderate Recovery'
    return 'Low Recovery'
  }

  return (
    <div className="flex items-center gap-3 p-3 bg-secondary-50 rounded-lg mb-4">
      <div className="flex-1">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-secondary-700">Recovery Score</span>
          <span className={clsx(
            'text-sm font-bold',
            score >= 70 ? 'text-success-600' : score >= 40 ? 'text-accent-600' : 'text-destructive-600'
          )}>
            {score}/100
          </span>
        </div>
        <div className="h-2 bg-secondary-200 rounded-full overflow-hidden">
          <div
            className={clsx('h-full transition-all duration-500', getColor())}
            style={{ width: `${score}%` }}
          />
        </div>
        <div className="text-xs text-secondary-500 mt-1">{getLabel()}</div>
      </div>
    </div>
  )
}

const StreamingFeedback: React.FC<StreamingFeedbackProps> = ({
  content,
  recoveryScore,
  isStreaming,
  error,
}) => {
  return (
    <div className="space-y-4">
      {/* Recovery Score Gauge */}
      {recoveryScore !== null && <RecoveryGauge score={recoveryScore} />}

      {/* Streaming Content */}
      <div className="relative">
        {isStreaming && (
          <div className="absolute top-2 right-2">
            <Spinner size="sm" />
          </div>
        )}

        <div
          className={clsx(
            'p-4 bg-white border border-secondary-200 rounded-lg min-h-[120px]',
            'prose prose-sm max-w-none',
            isStreaming && 'animate-pulse'
          )}
        >
          {content ? (
            <div className="whitespace-pre-wrap">{content}</div>
          ) : isStreaming ? (
            <div className="flex items-center gap-2 text-secondary-400">
              <span>Analyzing your session</span>
              <span className="animate-pulse">...</span>
            </div>
          ) : (
            <div className="text-secondary-400 italic">
              Click "Adapt Session" to get personalized recommendations based on your current state.
            </div>
          )}
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-3 bg-destructive-50 border border-destructive-200 rounded-lg text-destructive-700 text-sm">
          {error}
        </div>
      )}

      {/* Streaming indicator */}
      {isStreaming && (
        <div className="flex items-center gap-2 text-xs text-secondary-500">
          <div className="flex gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
          <span>AI is thinking...</span>
        </div>
      )}
    </div>
  )
}

export default StreamingFeedback

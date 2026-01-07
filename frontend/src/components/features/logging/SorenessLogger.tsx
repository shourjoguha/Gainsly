import React, { useState } from 'react'
import { clsx } from 'clsx'
import { Button, Alert } from '../../common'
import { BODY_PARTS, SORENESS_LEVELS } from '../../../utils/constants'
import { loggingApi } from '../../../api/logging'
import type { SorenessLogCreate } from '../../../types/api'
import { CheckCircleIcon } from '@heroicons/react/24/outline'

interface SorenessLoggerProps {
  onSuccess?: () => void
  onCancel?: () => void
}

const SorenessLogger: React.FC<SorenessLoggerProps> = ({ onSuccess, onCancel }) => {
  const [soreness, setSoreness] = useState<Record<string, number>>({})
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSorenessChange = (bodyPart: string, level: number) => {
    setSoreness(prev => {
      if (level === 0) {
        const { [bodyPart]: _, ...rest } = prev
        return rest
      }
      return { ...prev, [bodyPart]: level }
    })
  }

  const handleSubmit = async () => {
    setError(null)
    setIsSubmitting(true)

    try {
      const entries = Object.entries(soreness)
        .filter(([_, level]) => level > 0)
        .map(([body_part, soreness_1_5]) => ({
          body_part,
          soreness_1_5,
          notes: notes[body_part] || undefined,
        })) as SorenessLogCreate[]

      if (entries.length === 0) {
        setError('Please log at least one body part')
        setIsSubmitting(false)
        return
      }

      await loggingApi.createSorenessBatch(entries)
      setSuccess(true)

      setTimeout(() => {
        onSuccess?.()
      }, 1500)
    } catch (err: any) {
      setError(err.message || 'Failed to log soreness')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (success) {
    return (
      <div className="text-center py-8">
        <CheckCircleIcon className="w-16 h-16 mx-auto text-success-500 mb-4" />
        <h3 className="text-lg font-semibold text-secondary-900">Soreness Logged!</h3>
        <p className="text-secondary-600">Thanks for tracking how you feel.</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="error" dismissible onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      <p className="text-sm text-secondary-600">
        Rate your soreness for each muscle group. Click multiple times to cycle through levels.
      </p>

      {/* Legend */}
      <div className="flex flex-wrap gap-2 text-xs">
        {SORENESS_LEVELS.map(level => (
          <span
            key={level.value}
            className={clsx(
              'px-2 py-1 rounded border',
              level.value === 1 && 'bg-success-50 border-success-200 text-success-700',
              level.value === 2 && 'bg-success-100 border-success-300 text-success-800',
              level.value === 3 && 'bg-accent-100 border-accent-300 text-accent-800',
              level.value === 4 && 'bg-destructive-100 border-destructive-300 text-destructive-700',
              level.value === 5 && 'bg-destructive-200 border-destructive-400 text-destructive-800'
            )}
          >
            {level.value}: {level.label}
          </span>
        ))}
      </div>

      {/* Body Parts Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {BODY_PARTS.map(part => {
          const level = soreness[part] || 0
          return (
            <button
              key={part}
              type="button"
              onClick={() => handleSorenessChange(part, (level + 1) % 6)}
              className={clsx(
                'p-3 rounded-lg border-2 text-left transition-all text-sm',
                level === 0 && 'bg-secondary-50 border-secondary-200 text-secondary-600',
                level === 1 && 'bg-success-50 border-success-300 text-success-700',
                level === 2 && 'bg-success-100 border-success-400 text-success-800',
                level === 3 && 'bg-accent-100 border-accent-400 text-accent-800',
                level === 4 && 'bg-destructive-100 border-destructive-400 text-destructive-700',
                level === 5 && 'bg-destructive-200 border-destructive-500 text-destructive-800'
              )}
            >
              <div className="font-medium capitalize">
                {part.replace('_', ' ')}
              </div>
              <div className="text-xs mt-1">
                {level > 0
                  ? SORENESS_LEVELS.find(l => l.value === level)?.label
                  : 'Not rated'}
              </div>
            </button>
          )
        })}
      </div>

      {/* Notes for selected parts */}
      {Object.keys(soreness).length > 0 && (
        <div className="space-y-3">
          <label className="block text-sm font-medium text-secondary-700">
            Optional notes for sore areas
          </label>
          {Object.entries(soreness)
            .filter(([_, level]) => level > 2)
            .map(([part]) => (
              <div key={part} className="flex items-start gap-3">
                <span className="text-sm text-secondary-600 capitalize w-24">
                  {part.replace('_', ' ')}:
                </span>
                <input
                  type="text"
                  className="flex-1 px-3 py-1.5 text-sm border border-secondary-300 rounded-input focus:outline-none focus:ring-2 focus:ring-primary-500/20"
                  placeholder="What might have caused this?"
                  value={notes[part] || ''}
                  onChange={e => setNotes(prev => ({ ...prev, [part]: e.target.value }))}
                />
              </div>
            ))}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-3 pt-4 border-t border-secondary-200">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button
          fullWidth
          loading={isSubmitting}
          onClick={handleSubmit}
          disabled={Object.keys(soreness).length === 0}
        >
          Log Soreness ({Object.keys(soreness).length} areas)
        </Button>
      </div>
    </div>
  )
}

export default SorenessLogger

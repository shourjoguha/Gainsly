import React, { useState } from 'react'
import { Button, Input, Alert } from '../../common'
import type { WorkoutLogCreate, TopSetCreate, SessionResponse } from '../../../types/api'
import { loggingApi } from '../../../api/logging'
import { PlusIcon, TrashIcon, CheckCircleIcon } from '@heroicons/react/24/outline'

interface WorkoutLogFormProps {
  session?: SessionResponse | null
  sessionId?: number
  onSuccess?: () => void
  onCancel?: () => void
}

interface TopSetFormData extends TopSetCreate {
  movementName?: string
}

const WorkoutLogForm: React.FC<WorkoutLogFormProps> = ({
  session,
  sessionId,
  onSuccess,
  onCancel,
}) => {
  const [topSets, setTopSets] = useState<TopSetFormData[]>([])
  const [notes, setNotes] = useState('')
  const [perceivedExertion, setPerceivedExertion] = useState('')
  const [perceivedDifficulty, setPerceivedDifficulty] = useState('')
  const [adherence, setAdherence] = useState('')
  const [actualDuration, setActualDuration] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // Add movement from session main exercises
  const sessionMovements = session?.main?.map((ex, i) => ({
    id: ex.movement_id || i,
    name: ex.movement,
  })) || []

  const addTopSet = () => {
    setTopSets(prev => [
      ...prev,
      { movement_id: 0, weight: 0, reps: 0, movementName: '' },
    ])
  }

  const removeTopSet = (index: number) => {
    setTopSets(prev => prev.filter((_, i) => i !== index))
  }

  const updateTopSet = (index: number, field: keyof TopSetFormData, value: any) => {
    setTopSets(prev => prev.map((set, i) => (i === index ? { ...set, [field]: value } : set)))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)

    try {
      const logData: WorkoutLogCreate = {
        session_id: sessionId || session?.id,
        completed: true,
        top_sets: topSets
          .filter(s => s.movement_id > 0 && s.weight > 0 && s.reps > 0)
          .map(({ movementName, ...rest }) => rest),
        notes: notes || undefined,
        perceived_exertion: perceivedExertion ? parseInt(perceivedExertion) : undefined,
        perceived_difficulty: perceivedDifficulty ? parseInt(perceivedDifficulty) : undefined,
        adherence_percentage: adherence ? parseInt(adherence) : undefined,
        actual_duration_minutes: actualDuration ? parseInt(actualDuration) : undefined,
      }

      await loggingApi.createWorkout(logData)
      setSuccess(true)

      setTimeout(() => {
        onSuccess?.()
      }, 1500)
    } catch (err: any) {
      setError(err.message || 'Failed to log workout')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (success) {
    return (
      <div className="text-center py-8">
        <CheckCircleIcon className="w-16 h-16 mx-auto text-success-500 mb-4" />
        <h3 className="text-lg font-semibold text-secondary-900">Workout Logged!</h3>
        <p className="text-secondary-600">Great job completing your session.</p>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <Alert variant="error" dismissible onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Top Sets */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <label className="block text-sm font-medium text-secondary-700">
            Top Sets (best set per movement)
          </label>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={addTopSet}
            leftIcon={<PlusIcon className="w-4 h-4" />}
          >
            Add Set
          </Button>
        </div>

        {topSets.length === 0 ? (
          <div className="text-center py-6 bg-secondary-50 rounded-lg text-secondary-500 text-sm">
            No top sets logged yet. Click "Add Set" to record your best set for each movement.
          </div>
        ) : (
          <div className="space-y-3">
            {topSets.map((set, index) => (
              <div
                key={index}
                className="flex items-end gap-3 p-3 bg-secondary-50 rounded-lg"
              >
                <div className="flex-1">
                  <label className="block text-xs text-secondary-600 mb-1">Movement</label>
                  {sessionMovements.length > 0 ? (
                    <select
                      className="w-full px-3 py-2 text-sm border border-secondary-300 rounded-input focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                      value={set.movement_id}
                      onChange={e => updateTopSet(index, 'movement_id', parseInt(e.target.value))}
                    >
                      <option value={0}>Select movement...</option>
                      {sessionMovements.map(m => (
                        <option key={m.id} value={m.id}>
                          {m.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <Input
                      placeholder="Movement ID"
                      type="number"
                      value={set.movement_id || ''}
                      onChange={e => updateTopSet(index, 'movement_id', parseInt(e.target.value))}
                    />
                  )}
                </div>
                <div className="w-24">
                  <label className="block text-xs text-secondary-600 mb-1">Weight</label>
                  <Input
                    type="number"
                    step="0.5"
                    placeholder="kg/lbs"
                    value={set.weight || ''}
                    onChange={e => updateTopSet(index, 'weight', parseFloat(e.target.value))}
                  />
                </div>
                <div className="w-20">
                  <label className="block text-xs text-secondary-600 mb-1">Reps</label>
                  <Input
                    type="number"
                    placeholder="0"
                    value={set.reps || ''}
                    onChange={e => updateTopSet(index, 'reps', parseInt(e.target.value))}
                  />
                </div>
                <div className="w-16">
                  <label className="block text-xs text-secondary-600 mb-1">RPE</label>
                  <Input
                    type="number"
                    min="1"
                    max="10"
                    step="0.5"
                    placeholder="8"
                    value={set.rpe || ''}
                    onChange={e => updateTopSet(index, 'rpe', parseFloat(e.target.value))}
                  />
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => removeTopSet(index)}
                  className="text-destructive-500 hover:text-destructive-600"
                >
                  <TrashIcon className="w-4 h-4" />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Subjective Metrics */}
      <div>
        <label className="block text-sm font-medium text-secondary-700 mb-3">
          How was the session?
        </label>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-secondary-600 mb-1">
              Exertion: {perceivedExertion || '-'}/10
            </label>
            <input
              type="range"
              min="1"
              max="10"
              value={perceivedExertion || 5}
              onChange={e => setPerceivedExertion(e.target.value)}
              className="w-full"
            />
          </div>
          <div>
            <label className="block text-xs text-secondary-600 mb-1">
              Difficulty: {perceivedDifficulty || '-'}/10
            </label>
            <input
              type="range"
              min="1"
              max="10"
              value={perceivedDifficulty || 5}
              onChange={e => setPerceivedDifficulty(e.target.value)}
              className="w-full"
            />
          </div>
        </div>
      </div>

      {/* Additional Fields */}
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Adherence %"
          type="number"
          min="0"
          max="100"
          placeholder="100"
          value={adherence}
          onChange={e => setAdherence(e.target.value)}
          helpText="How much of the plan did you complete?"
        />
        <Input
          label="Actual Duration"
          type="number"
          placeholder="60"
          value={actualDuration}
          onChange={e => setActualDuration(e.target.value)}
          helpText="Minutes"
        />
      </div>

      {/* Notes */}
      <div>
        <label className="block text-xs font-medium text-secondary-700 mb-1">
          Notes
        </label>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="How did the session feel? Any observations?"
          rows={3}
          className="w-full px-3 py-2 text-sm border border-secondary-300 rounded-input focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
        />
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-4 border-t border-secondary-200">
        {onCancel && (
          <Button type="button" variant="secondary" onClick={onCancel}>
            Cancel
          </Button>
        )}
        <Button type="submit" fullWidth loading={isSubmitting}>
          Log Workout
        </Button>
      </div>
    </form>
  )
}

export default WorkoutLogForm

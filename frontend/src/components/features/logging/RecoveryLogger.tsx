import React, { useState } from 'react'
import { Button, Input, Select, Alert } from '../../common'
import { RECOVERY_SOURCES } from '../../../utils/constants'
import { loggingApi } from '../../../api/logging'
import type { RecoverySignalCreate, RecoverySource } from '../../../types/api'
import { CheckCircleIcon } from '@heroicons/react/24/outline'

interface RecoveryLoggerProps {
  onSuccess?: () => void
  onCancel?: () => void
}

const RecoveryLogger: React.FC<RecoveryLoggerProps> = ({ onSuccess, onCancel }) => {
  const [source, setSource] = useState<string>('MANUAL')
  const [sleepHours, setSleepHours] = useState('')
  const [sleepScore, setSleepScore] = useState('')
  const [hrv, setHrv] = useState('')
  const [restingHr, setRestingHr] = useState('')
  const [readiness, setReadiness] = useState('')
  const [notes, setNotes] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async () => {
    setError(null)
    setIsSubmitting(true)

    try {
      const data: RecoverySignalCreate = {
        source: source as RecoverySource,
        sleep_hours: sleepHours ? parseFloat(sleepHours) : undefined,
        sleep_score: sleepScore ? parseInt(sleepScore) : undefined,
        hrv: hrv ? parseFloat(hrv) : undefined,
        resting_hr: restingHr ? parseInt(restingHr) : undefined,
        readiness: readiness ? parseInt(readiness) : undefined,
        notes: notes || undefined,
      }

      // Validate at least one metric is provided
      if (!data.sleep_hours && !data.sleep_score && !data.hrv && !data.resting_hr && !data.readiness) {
        setError('Please provide at least one recovery metric')
        setIsSubmitting(false)
        return
      }

      await loggingApi.createRecovery(data)
      setSuccess(true)

      setTimeout(() => {
        onSuccess?.()
      }, 1500)
    } catch (err: any) {
      setError(err.message || 'Failed to log recovery')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (success) {
    return (
      <div className="text-center py-8">
        <CheckCircleIcon className="w-16 h-16 mx-auto text-success-500 mb-4" />
        <h3 className="text-lg font-semibold text-secondary-900">Recovery Logged!</h3>
        <p className="text-secondary-600">Your recovery data has been recorded.</p>
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

      {/* Data Source */}
      <Select
        label="Data Source"
        options={RECOVERY_SOURCES.map(s => ({ value: s.value, label: s.label }))}
        value={source}
        onChange={e => setSource(e.target.value)}
        helpText="Where is this data from?"
      />

      {/* Sleep Metrics */}
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-secondary-700">Sleep</h3>
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Hours Slept"
            type="number"
            step="0.25"
            min="0"
            max="24"
            placeholder="7.5"
            value={sleepHours}
            onChange={e => setSleepHours(e.target.value)}
          />
          <Input
            label="Sleep Score"
            type="number"
            min="0"
            max="100"
            placeholder="85"
            value={sleepScore}
            onChange={e => setSleepScore(e.target.value)}
            helpText="0-100 if from wearable"
          />
        </div>
      </div>

      {/* HRV & HR Metrics */}
      <div className="space-y-4">
        <h3 className="text-sm font-medium text-secondary-700">Heart Rate Variability</h3>
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="HRV (ms)"
            type="number"
            step="0.1"
            min="0"
            placeholder="45"
            value={hrv}
            onChange={e => setHrv(e.target.value)}
            helpText="RMSSD in milliseconds"
          />
          <Input
            label="Resting HR"
            type="number"
            min="30"
            max="200"
            placeholder="55"
            value={restingHr}
            onChange={e => setRestingHr(e.target.value)}
            helpText="Beats per minute"
          />
        </div>
      </div>

      {/* Readiness Score */}
      <div>
        <label className="block text-xs font-medium text-secondary-700 mb-1">
          Readiness Score: {readiness || '-'}/100
        </label>
        <input
          type="range"
          min="0"
          max="100"
          value={readiness || 50}
          onChange={e => setReadiness(e.target.value)}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-secondary-500 mt-1">
          <span>Low readiness</span>
          <span>High readiness</span>
        </div>
      </div>

      {/* Notes */}
      <div>
        <label className="block text-xs font-medium text-secondary-700 mb-1">
          Notes
        </label>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Any additional context about how you're feeling..."
          rows={2}
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
        <Button fullWidth loading={isSubmitting} onClick={handleSubmit}>
          Log Recovery
        </Button>
      </div>
    </div>
  )
}

export default RecoveryLogger

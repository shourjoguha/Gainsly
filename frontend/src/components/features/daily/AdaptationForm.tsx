import React, { useState } from 'react'
import { clsx } from 'clsx'
import { Button, Select, Input } from '../../common'
import {
  ADAPTATION_PREFERENCES,
  ADHERENCE_OPTIONS,
  BODY_PARTS,
  SLEEP_QUALITY,
} from '../../../utils/constants'
import type { AdaptationRequest, SorenessInput, RecoveryInput } from '../../../types/api'
import { AdjustmentsHorizontalIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline'

interface AdaptationFormProps {
  programId: number
  onSubmit: (data: AdaptationRequest) => void
  isLoading: boolean
}

const AdaptationForm: React.FC<AdaptationFormProps> = ({ programId, onSubmit, isLoading }) => {
  const [expanded, setExpanded] = useState(false)
  const [formData, setFormData] = useState<{
    timeAvailable: string
    preference: string
    adherence: string
    excludedMovements: string
    focusForToday: string
    sleepQuality: string
    sleepHours: string
    energyLevel: string
    stressLevel: string
    soreness: Record<string, number>
    activityYesterday: string
    userMessage: string
  }>({
    timeAvailable: '',
    preference: 'any',
    adherence: 'balanced',
    excludedMovements: '',
    focusForToday: '',
    sleepQuality: '',
    sleepHours: '',
    energyLevel: '',
    stressLevel: '',
    soreness: {},
    activityYesterday: '',
    userMessage: '',
  })

  const handleSorenessChange = (bodyPart: string, level: number) => {
    setFormData(prev => ({
      ...prev,
      soreness: level === 0
        ? Object.fromEntries(Object.entries(prev.soreness).filter(([k]) => k !== bodyPart))
        : { ...prev.soreness, [bodyPart]: level },
    }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    const sorenessInputs: SorenessInput[] = Object.entries(formData.soreness)
      .filter(([_, level]) => level > 0)
      .map(([body_part, level]) => ({ body_part, level }))

    const recoveryInput: RecoveryInput | undefined = (
      formData.sleepQuality || formData.sleepHours || formData.energyLevel || formData.stressLevel
    ) ? {
      sleep_quality: formData.sleepQuality as RecoveryInput['sleep_quality'] || undefined,
      sleep_hours: formData.sleepHours ? parseFloat(formData.sleepHours) : undefined,
      energy_level: formData.energyLevel ? parseInt(formData.energyLevel) : undefined,
      stress_level: formData.stressLevel ? parseInt(formData.stressLevel) : undefined,
    } : undefined

    const request: AdaptationRequest = {
      program_id: programId,
      time_available_minutes: formData.timeAvailable ? parseInt(formData.timeAvailable) : undefined,
      preference: formData.preference as AdaptationRequest['preference'],
      adherence_vs_optimality: formData.adherence as AdaptationRequest['adherence_vs_optimality'],
      excluded_movements: formData.excludedMovements
        ? formData.excludedMovements.split(',').map(s => s.trim()).filter(Boolean)
        : undefined,
      focus_for_today: formData.focusForToday || undefined,
      soreness: sorenessInputs.length > 0 ? sorenessInputs : undefined,
      recovery: recoveryInput,
      activity_yesterday: formData.activityYesterday || undefined,
      user_message: formData.userMessage || undefined,
    }

    onSubmit(request)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Quick options - always visible */}
      <div className="grid grid-cols-2 gap-4">
        <Input
          label="Time Available"
          type="number"
          placeholder="60"
          value={formData.timeAvailable}
          onChange={e => setFormData(prev => ({ ...prev, timeAvailable: e.target.value }))}
          helpText="Minutes"
        />

        <Select
          label="Preference"
          options={ADAPTATION_PREFERENCES.map(p => ({ value: p.value, label: p.label }))}
          value={formData.preference}
          onChange={e => setFormData(prev => ({ ...prev, preference: e.target.value }))}
        />
      </div>

      <Select
        label="Mode"
        options={ADHERENCE_OPTIONS.map(a => ({ value: a.value, label: `${a.label} - ${a.description}` }))}
        value={formData.adherence}
        onChange={e => setFormData(prev => ({ ...prev, adherence: e.target.value }))}
      />

      {/* Expandable advanced options */}
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm text-secondary-600 hover:text-secondary-900 transition-colors"
      >
        <AdjustmentsHorizontalIcon className="w-4 h-4" />
        <span>Advanced Options</span>
        {expanded ? <ChevronUpIcon className="w-4 h-4" /> : <ChevronDownIcon className="w-4 h-4" />}
      </button>

      {expanded && (
        <div className="space-y-4 pt-2 border-t border-secondary-200">
          {/* Recovery Inputs */}
          <div className="grid grid-cols-2 gap-4">
            <Select
              label="Sleep Quality"
              options={[{ value: '', label: 'Select...' }, ...SLEEP_QUALITY.map(s => ({ value: s.value, label: s.label }))]}
              value={formData.sleepQuality}
              onChange={e => setFormData(prev => ({ ...prev, sleepQuality: e.target.value }))}
            />

            <Input
              label="Sleep Hours"
              type="number"
              step="0.5"
              min="0"
              max="24"
              placeholder="7.5"
              value={formData.sleepHours}
              onChange={e => setFormData(prev => ({ ...prev, sleepHours: e.target.value }))}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-secondary-700 mb-1">
                Energy Level: {formData.energyLevel || '-'}/10
              </label>
              <input
                type="range"
                min="1"
                max="10"
                value={formData.energyLevel || 5}
                onChange={e => setFormData(prev => ({ ...prev, energyLevel: e.target.value }))}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-secondary-700 mb-1">
                Stress Level: {formData.stressLevel || '-'}/10
              </label>
              <input
                type="range"
                min="1"
                max="10"
                value={formData.stressLevel || 5}
                onChange={e => setFormData(prev => ({ ...prev, stressLevel: e.target.value }))}
                className="w-full"
              />
            </div>
          </div>

          {/* Soreness Input */}
          <div>
            <label className="block text-xs font-medium text-secondary-700 mb-2">
              Muscle Soreness (click to rate)
            </label>
            <div className="flex flex-wrap gap-2">
              {BODY_PARTS.map(part => {
                const level = formData.soreness[part] || 0
                return (
                  <button
                    key={part}
                    type="button"
                    onClick={() => handleSorenessChange(part, (level + 1) % 6)}
                    className={clsx(
                      'px-2 py-1 text-xs rounded border transition-colors',
                      level === 0 && 'bg-secondary-50 border-secondary-200 text-secondary-600',
                      level === 1 && 'bg-success-50 border-success-200 text-success-700',
                      level === 2 && 'bg-success-100 border-success-300 text-success-800',
                      level === 3 && 'bg-accent-100 border-accent-300 text-accent-800',
                      level === 4 && 'bg-destructive-100 border-destructive-300 text-destructive-700',
                      level === 5 && 'bg-destructive-200 border-destructive-400 text-destructive-800'
                    )}
                  >
                    {part.replace('_', ' ')} {level > 0 && `(${level})`}
                  </button>
                )
              })}
            </div>
            <div className="text-xs text-secondary-500 mt-1">
              0 = none, 5 = severe. Click to cycle.
            </div>
          </div>

          {/* Other inputs */}
          <Input
            label="Excluded Movements"
            placeholder="squat, deadlift"
            value={formData.excludedMovements}
            onChange={e => setFormData(prev => ({ ...prev, excludedMovements: e.target.value }))}
            helpText="Comma-separated list of movements to avoid"
          />

          <Input
            label="Activity Yesterday"
            placeholder="hiking, tennis, etc."
            value={formData.activityYesterday}
            onChange={e => setFormData(prev => ({ ...prev, activityYesterday: e.target.value }))}
          />

          <Input
            label="Focus for Today"
            placeholder="e.g., upper body strength, recovery"
            value={formData.focusForToday}
            onChange={e => setFormData(prev => ({ ...prev, focusForToday: e.target.value }))}
          />

          <div>
            <label className="block text-xs font-medium text-secondary-700 mb-1">
              Additional Notes for Coach
            </label>
            <textarea
              value={formData.userMessage}
              onChange={e => setFormData(prev => ({ ...prev, userMessage: e.target.value }))}
              placeholder="Any other context you want to share..."
              rows={2}
              className="w-full px-3 py-2 text-sm border border-secondary-300 rounded-input focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
            />
          </div>
        </div>
      )}

      <Button type="submit" fullWidth loading={isLoading}>
        Adapt Session
      </Button>
    </form>
  )
}

export default AdaptationForm

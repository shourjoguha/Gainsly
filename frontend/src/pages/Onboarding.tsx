import React, { useState, useCallback } from 'react'
import { clsx } from 'clsx'
import { useNavigate } from '@tanstack/react-router'
import { Button, Card, CardContent, Alert, Select } from '../components/common'
import GoalSelector from '../components/features/program/GoalSelector'
import { programsApi } from '../api'
import {
  SPLIT_TEMPLATES,
  PROGRESSION_STYLES,
  DELOAD_FREQUENCIES,
  PROGRAM_DURATION,
} from '../utils/constants'
import type { GoalWeight, SplitTemplate, ProgressionStyle, ProgramCreate } from '../types/api'
import { ArrowLeftIcon, ArrowRightIcon, CheckIcon } from '@heroicons/react/24/outline'

type Step = 'goals' | 'structure' | 'preferences' | 'review'

const STEPS: { key: Step; label: string }[] = [
  { key: 'goals', label: 'Goals' },
  { key: 'structure', label: 'Structure' },
  { key: 'preferences', label: 'Preferences' },
  { key: 'review', label: 'Review' },
]

interface FormData {
  goals: GoalWeight[]
  split_template: SplitTemplate | ''
  progression_style: ProgressionStyle | ''
  duration_weeks: number
  deload_every_n_microcycles: number
}

const Onboarding: React.FC = () => {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState<Step>('goals')
  const [formData, setFormData] = useState<FormData>({
    goals: [],
    split_template: '',
    progression_style: '',
    duration_weeks: PROGRAM_DURATION.default,
    deload_every_n_microcycles: 4,
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  const currentStepIndex = STEPS.findIndex(s => s.key === currentStep)

  const handleGoalsChange = useCallback((goals: GoalWeight[]) => {
    setFormData(prev => ({ ...prev, goals }))
  }, [])

  const validateStep = (step: Step): boolean => {
    switch (step) {
      case 'goals':
        const totalWeight = formData.goals.reduce((sum, g) => sum + g.weight, 0)
        return formData.goals.length === 3 && totalWeight === 10
      case 'structure':
        return formData.split_template !== '' && formData.progression_style !== ''
      case 'preferences':
        return formData.duration_weeks >= 8 && formData.duration_weeks <= 12
      case 'review':
        return true
      default:
        return false
    }
  }

  const goNext = () => {
    const nextIndex = currentStepIndex + 1
    if (nextIndex < STEPS.length) {
      setCurrentStep(STEPS[nextIndex].key)
    }
  }

  const goPrev = () => {
    const prevIndex = currentStepIndex - 1
    if (prevIndex >= 0) {
      setCurrentStep(STEPS[prevIndex].key)
    }
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)
    setError(null)

    try {
      const programData: ProgramCreate = {
        goals: formData.goals,
        split_template: formData.split_template as SplitTemplate,
        progression_style: formData.progression_style as ProgressionStyle,
        duration_weeks: formData.duration_weeks,
        deload_every_n_microcycles: formData.deload_every_n_microcycles,
      }

      await programsApi.create(programData)
      setSuccess(true)

      // Redirect to daily plan after brief delay
      setTimeout(() => {
        navigate({ to: '/daily' })
      }, 2000)
    } catch (err: any) {
      console.error('Program creation error:', err)
      let msg = 'Failed to create program'
      if (typeof err.message === 'string') {
        msg = err.message
      } else if (err.data?.detail) {
        msg = JSON.stringify(err.data.detail)
      }
      setError(msg)
    } finally {
      setIsSubmitting(false)
    }
  }

  const getSplitLabel = (value: string) => SPLIT_TEMPLATES.find(s => s.value === value)?.label || value
  const getProgressionLabel = (value: string) => PROGRESSION_STYLES.find(s => s.value === value)?.label || value

  if (success) {
    return (
      <div className="max-w-2xl mx-auto text-center py-12">
        <div className="w-16 h-16 bg-success-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <CheckIcon className="w-8 h-8 text-success-600" />
        </div>
        <h1 className="text-2xl font-bold text-secondary-900 mb-2">Program Created!</h1>
        <p className="text-secondary-600">Redirecting you to your dashboard...</p>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-secondary-900 mb-2">Create Your Program</h1>
      <p className="text-secondary-600 mb-6">
        Set up your personalized training program in a few simple steps.
      </p>

      {/* Progress Steps */}
      <div className="flex items-center justify-between mb-8">
        {STEPS.map((step, index) => (
          <React.Fragment key={step.key}>
            <div className="flex items-center">
              <div
                className={clsx(
                  'w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium',
                  index < currentStepIndex
                    ? 'bg-primary-500 text-white'
                    : index === currentStepIndex
                    ? 'bg-primary-500 text-white'
                    : 'bg-secondary-200 text-secondary-600'
                )}
              >
                {index < currentStepIndex ? (
                  <CheckIcon className="w-4 h-4" />
                ) : (
                  index + 1
                )}
              </div>
              <span
                className={clsx(
                  'ml-2 text-sm hidden sm:block',
                  index <= currentStepIndex ? 'text-secondary-900' : 'text-secondary-400'
                )}
              >
                {step.label}
              </span>
            </div>
            {index < STEPS.length - 1 && (
              <div
                className={clsx(
                  'flex-1 h-0.5 mx-2',
                  index < currentStepIndex ? 'bg-primary-500' : 'bg-secondary-200'
                )}
              />
            )}
          </React.Fragment>
        ))}
      </div>

      {error && (
        <Alert variant="error" className="mb-4" dismissible onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Card>
        <CardContent>
          {/* Step 1: Goals */}
          {currentStep === 'goals' && (
            <div>
              <h2 className="text-lg font-bold mb-4">What are your fitness goals?</h2>
              <p className="text-secondary-600 mb-4">
                Select 3 goals and distribute 10 points across them based on priority.
                This uses the "Ten-Dollar Method" to balance your training focus.
              </p>
              <GoalSelector
                value={formData.goals}
                onChange={handleGoalsChange}
              />
            </div>
          )}

          {/* Step 2: Structure */}
          {currentStep === 'structure' && (
            <div className="space-y-6">
              <h2 className="text-lg font-bold mb-4">How do you want to train?</h2>

              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">
                  Split Template
                </label>
                <div className="grid gap-3">
                  {SPLIT_TEMPLATES.map((template) => (
                    <button
                      key={template.value}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, split_template: template.value as SplitTemplate }))}
                      className={clsx(
                        'p-4 rounded-lg border-2 text-left transition-all',
                        formData.split_template === template.value
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-secondary-200 hover:border-secondary-300'
                      )}
                    >
                      <div className="font-medium">{template.label}</div>
                      <div className="text-sm text-secondary-500">{template.description}</div>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">
                  Progression Style
                </label>
                <div className="grid gap-3">
                  {PROGRESSION_STYLES.map((style) => (
                    <button
                      key={style.value}
                      type="button"
                      onClick={() => setFormData(prev => ({ ...prev, progression_style: style.value as ProgressionStyle }))}
                      className={clsx(
                        'p-4 rounded-lg border-2 text-left transition-all',
                        formData.progression_style === style.value
                          ? 'border-primary-500 bg-primary-50'
                          : 'border-secondary-200 hover:border-secondary-300'
                      )}
                    >
                      <div className="font-medium">{style.label}</div>
                      <div className="text-sm text-secondary-500">{style.description}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Preferences */}
          {currentStep === 'preferences' && (
            <div className="space-y-6">
              <h2 className="text-lg font-bold mb-4">Program Preferences</h2>

              <div>
                <label className="block text-sm font-medium text-secondary-700 mb-2">
                  Program Duration: {formData.duration_weeks} weeks
                </label>
                <input
                  type="range"
                  min={PROGRAM_DURATION.min}
                  max={PROGRAM_DURATION.max}
                  value={formData.duration_weeks}
                  onChange={(e) => setFormData(prev => ({ ...prev, duration_weeks: parseInt(e.target.value) }))}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-secondary-500 mt-1">
                  <span>{PROGRAM_DURATION.min} weeks</span>
                  <span>{PROGRAM_DURATION.max} weeks</span>
                </div>
              </div>

              <Select
                label="Deload Frequency"
                options={DELOAD_FREQUENCIES.map(d => ({ value: String(d.value), label: d.label }))}
                value={String(formData.deload_every_n_microcycles)}
                onChange={(e) => setFormData(prev => ({ ...prev, deload_every_n_microcycles: parseInt(e.target.value) }))}
                helpText="How often to include a recovery week"
              />
            </div>
          )}

          {/* Step 4: Review */}
          {currentStep === 'review' && (
            <div className="space-y-4">
              <h2 className="text-lg font-bold mb-4">Review Your Program</h2>

              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b border-secondary-200">
                  <span className="text-secondary-600">Goals</span>
                  <span className="font-medium">
                    {formData.goals.map(g => `${g.goal} (${g.weight})`).join(', ')}
                  </span>
                </div>
                <div className="flex justify-between py-2 border-b border-secondary-200">
                  <span className="text-secondary-600">Split Template</span>
                  <span className="font-medium">{getSplitLabel(formData.split_template)}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-secondary-200">
                  <span className="text-secondary-600">Progression Style</span>
                  <span className="font-medium">{getProgressionLabel(formData.progression_style)}</span>
                </div>
                <div className="flex justify-between py-2 border-b border-secondary-200">
                  <span className="text-secondary-600">Duration</span>
                  <span className="font-medium">{formData.duration_weeks} weeks</span>
                </div>
                <div className="flex justify-between py-2">
                  <span className="text-secondary-600">Deload Frequency</span>
                  <span className="font-medium">Every {formData.deload_every_n_microcycles} weeks</span>
                </div>
              </div>
            </div>
          )}

          {/* Navigation */}
          <div className="flex justify-between mt-8 pt-4 border-t border-secondary-200">
            <Button
              variant="secondary"
              onClick={goPrev}
              disabled={currentStepIndex === 0}
              leftIcon={<ArrowLeftIcon className="w-4 h-4" />}
            >
              Back
            </Button>

            {currentStep !== 'review' ? (
              <Button
                onClick={goNext}
                disabled={!validateStep(currentStep)}
                rightIcon={<ArrowRightIcon className="w-4 h-4" />}
              >
                Next
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                loading={isSubmitting}
              >
                Create Program
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default Onboarding

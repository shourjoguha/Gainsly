import React from 'react'
import { clsx } from 'clsx'
import type { SessionResponse, ExerciseBlock, FinisherBlock } from '../../../types/api'
import { ClockIcon } from '@heroicons/react/24/outline'

interface SessionDetailsProps {
  session: SessionResponse
}

const ExerciseRow: React.FC<{ exercise: ExerciseBlock; index: number }> = ({ exercise, index }) => {
  const repsDisplay = exercise.rep_range_min && exercise.rep_range_max
    ? `${exercise.rep_range_min}-${exercise.rep_range_max}`
    : exercise.rep_range_min || exercise.rep_range_max || '—'

  return (
    <div className={clsx(
      'flex items-center gap-4 py-3',
      index > 0 && 'border-t border-secondary-100'
    )}>
      <div className="w-6 text-center text-sm text-secondary-400 font-mono">
        {index + 1}
      </div>
      <div className="flex-1">
        <div className="font-medium text-secondary-900">{exercise.movement}</div>
        {exercise.notes && (
          <div className="text-xs text-secondary-500 mt-0.5">{exercise.notes}</div>
        )}
      </div>
      <div className="text-sm text-secondary-600 font-mono">
        {exercise.sets} × {repsDisplay}
      </div>
      {exercise.target_rpe && (
        <div className="text-xs bg-accent-100 text-accent-700 px-2 py-0.5 rounded">
          RPE {exercise.target_rpe}
        </div>
      )}
      {exercise.target_rir !== undefined && exercise.target_rir !== null && (
        <div className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded">
          RIR {exercise.target_rir}
        </div>
      )}
    </div>
  )
}

const SectionBlock: React.FC<{
  title: string
  exercises?: ExerciseBlock[]
  duration?: number
  variant?: 'warmup' | 'main' | 'accessory' | 'finisher' | 'cooldown'
}> = ({ title, exercises, duration, variant = 'main' }) => {
  if (!exercises || exercises.length === 0) return null

  const variantStyles = {
    warmup: 'border-l-accent-400',
    main: 'border-l-primary-500',
    accessory: 'border-l-success-500',
    finisher: 'border-l-destructive-400',
    cooldown: 'border-l-secondary-400',
  }

  return (
    <div className={clsx('border-l-4 pl-4 mb-4', variantStyles[variant])}>
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-medium text-secondary-700 uppercase text-sm tracking-wide">
          {title}
        </h4>
        {duration && (
          <span className="flex items-center text-xs text-secondary-500">
            <ClockIcon className="w-3 h-3 mr-1" />
            {duration} min
          </span>
        )}
      </div>
      <div>
        {exercises.map((exercise, i) => (
          <ExerciseRow key={`${exercise.movement}-${i}`} exercise={exercise} index={i} />
        ))}
      </div>
    </div>
  )
}

const FinisherSection: React.FC<{ finisher: FinisherBlock; duration?: number }> = ({ finisher, duration }) => {
  return (
    <div className="border-l-4 border-l-destructive-400 pl-4 mb-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-medium text-secondary-700 uppercase text-sm tracking-wide">
          Finisher
        </h4>
        {duration && (
          <span className="flex items-center text-xs text-secondary-500">
            <ClockIcon className="w-3 h-3 mr-1" />
            {duration} min
          </span>
        )}
      </div>
      <div className="bg-destructive-50 rounded-lg p-3">
        <div className="font-medium text-destructive-900">{finisher.type}</div>
        {finisher.duration_minutes && (
          <div className="text-sm text-destructive-700">{finisher.duration_minutes} minutes</div>
        )}
        {finisher.rounds && (
          <div className="text-sm text-destructive-700">{finisher.rounds} rounds</div>
        )}
        {finisher.notes && (
          <div className="text-xs text-destructive-600 mt-1">{finisher.notes}</div>
        )}
        {finisher.exercises && finisher.exercises.length > 0 && (
          <div className="mt-2 space-y-1">
            {finisher.exercises.map((ex, i) => (
              <div key={i} className="text-sm text-destructive-800">
                • {ex.movement} {ex.sets && `× ${ex.sets}`}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

const SessionDetails: React.FC<SessionDetailsProps> = ({ session }) => {
  const totalDuration = session.estimated_duration_minutes || 
    (session.warmup_duration_minutes || 0) +
    (session.main_duration_minutes || 0) +
    (session.accessory_duration_minutes || 0) +
    (session.finisher_duration_minutes || 0) +
    (session.cooldown_duration_minutes || 0)

  return (
    <div className="space-y-4">
      {/* Session header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <span className="inline-block px-2 py-1 text-xs font-medium uppercase tracking-wide rounded bg-primary-100 text-primary-700">
            {session.session_type.replace('_', ' ')}
          </span>
          {session.intent_tags && session.intent_tags.length > 0 && (
            <div className="flex gap-1 mt-1">
              {session.intent_tags.map(tag => (
                <span key={tag} className="text-xs text-secondary-500">#{tag}</span>
              ))}
            </div>
          )}
        </div>
        {totalDuration > 0 && (
          <div className="flex items-center text-secondary-600">
            <ClockIcon className="w-5 h-5 mr-1" />
            <span className="font-mono">{totalDuration} min</span>
          </div>
        )}
      </div>

      {/* Coach notes */}
      {session.coach_notes && (
        <div className="bg-primary-50 rounded-lg p-3 text-sm text-primary-800 mb-4">
          <span className="font-medium">Coach:</span> {session.coach_notes}
        </div>
      )}

      {/* Session sections */}
      <SectionBlock
        title="Warm-up"
        exercises={session.warmup}
        duration={session.warmup_duration_minutes}
        variant="warmup"
      />

      <SectionBlock
        title="Main Work"
        exercises={session.main}
        duration={session.main_duration_minutes}
        variant="main"
      />

      <SectionBlock
        title="Accessories"
        exercises={session.accessory}
        duration={session.accessory_duration_minutes}
        variant="accessory"
      />

      {session.finisher && (
        <FinisherSection
          finisher={session.finisher}
          duration={session.finisher_duration_minutes}
        />
      )}

      <SectionBlock
        title="Cool-down"
        exercises={session.cooldown}
        duration={session.cooldown_duration_minutes}
        variant="cooldown"
      />
    </div>
  )
}

export default SessionDetails

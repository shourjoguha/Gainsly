import React from 'react'
import { clsx } from 'clsx'
import { Link } from '@tanstack/react-router'
import { Card, CardContent, Button } from '../../common'
import type { ProgramResponse } from '../../../types/api'
import {
  CalendarIcon,
  ChartBarIcon,
  CheckCircleIcon,
  PlayIcon,
} from '@heroicons/react/24/outline'

interface ProgramCardProps {
  program: ProgramResponse
  onSelect?: (program: ProgramResponse) => void
  isActive?: boolean
}

const ProgramCard: React.FC<ProgramCardProps> = ({ program, onSelect, isActive }) => {
  const formatGoals = () => {
    const goals = [
      { goal: program.goal_1, weight: program.goal_weight_1 },
      { goal: program.goal_2, weight: program.goal_weight_2 },
      { goal: program.goal_3, weight: program.goal_weight_3 },
    ].filter(g => g.goal && g.weight > 0)

    return goals.map(g => (
      <span key={g.goal} className="inline-flex items-center gap-1 text-xs">
        <span className="capitalize">{g.goal}</span>
        <span className="text-secondary-400">({g.weight})</span>
      </span>
    ))
  }

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'Not started'
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    })
  }

  const getSplitLabel = (split: string) => {
    switch (split) {
      case 'UPPER_LOWER': return 'Upper/Lower'
      case 'PPL': return 'Push/Pull/Legs'
      case 'FULL_BODY': return 'Full Body'
      case 'HYBRID': return 'Hybrid'
      default: return split
    }
  }

  const getProgressionLabel = (progression: string) => {
    switch (progression) {
      case 'SINGLE': return 'Single'
      case 'DOUBLE': return 'Double'
      case 'PAUSED_VARIATIONS': return 'Paused'
      case 'BUILD_TO_DROP': return 'Build to Drop'
      default: return progression
    }
  }

  return (
    <Card className={clsx(
      'transition-all',
      isActive && 'ring-2 ring-primary-500',
      onSelect && 'cursor-pointer hover:shadow-md'
    )}>
      <CardContent>
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-semibold text-secondary-900">
                {getSplitLabel(program.split_template)} Program
              </h3>
              {program.is_active && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium bg-success-100 text-success-700 rounded-full">
                  <PlayIcon className="w-3 h-3" />
                  Active
                </span>
              )}
            </div>
            <div className="flex items-center gap-2 text-sm text-secondary-600">
              <CalendarIcon className="w-4 h-4" />
              <span>{formatDate(program.program_start_date)}</span>
              <span className="text-secondary-300">•</span>
              <span>{program.duration_weeks} weeks</span>
            </div>
          </div>
        </div>

        {/* Goals */}
        <div className="mb-4">
          <div className="text-xs text-secondary-500 mb-1">Goals</div>
          <div className="flex flex-wrap gap-2">
            {formatGoals()}
          </div>
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-2 gap-4 text-sm mb-4">
          <div>
            <div className="text-xs text-secondary-500">Progression</div>
            <div className="font-medium">{getProgressionLabel(program.progression_style)}</div>
          </div>
          <div>
            <div className="text-xs text-secondary-500">Deload Every</div>
            <div className="font-medium">{program.deload_every_n_microcycles} weeks</div>
          </div>
        </div>

        {/* Persona */}
        {(program.persona_tone || program.persona_aggression) && (
          <div className="text-xs text-secondary-500 mb-4">
            Coach: <span className="capitalize">{program.persona_tone || 'neutral'}</span>
            {program.persona_aggression && (
              <span> / <span className="capitalize">{program.persona_aggression}</span></span>
            )}
          </div>
        )}

        {/* Actions */}
        {onSelect && (
          <div className="flex gap-2 pt-4 border-t border-secondary-200">
            <Button
              variant={isActive ? 'primary' : 'secondary'}
              size="sm"
              fullWidth
              onClick={() => onSelect(program)}
            >
              {isActive ? (
                <>
                  <CheckCircleIcon className="w-4 h-4 mr-1" />
                  Selected
                </>
              ) : (
                'Select'
              )}
            </Button>
            <Link to="/daily">
              <Button variant="ghost" size="sm">
                <ChartBarIcon className="w-4 h-4 mr-1" />
                View
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default ProgramCard

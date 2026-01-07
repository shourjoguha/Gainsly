import React, { useState, useEffect } from 'react'
import { clsx } from 'clsx'
import { GOALS } from '../../../utils/constants'
import type { Goal, GoalWeight } from '../../../types/api'

interface GoalSelectorProps {
  value: GoalWeight[]
  onChange: (goals: GoalWeight[]) => void
  error?: string
}

const GoalSelector: React.FC<GoalSelectorProps> = ({ value, onChange, error }) => {
  const [selectedGoals, setSelectedGoals] = useState<GoalWeight[]>(value)

  const totalWeight = selectedGoals.reduce((sum, g) => sum + g.weight, 0)
  const remainingWeight = 10 - totalWeight

  useEffect(() => {
    onChange(selectedGoals)
  }, [selectedGoals, onChange])

  const isGoalSelected = (goal: Goal) => selectedGoals.some(g => g.goal === goal)

  const toggleGoal = (goal: Goal) => {
    if (isGoalSelected(goal)) {
      // Remove goal
      setSelectedGoals(prev => prev.filter(g => g.goal !== goal))
    } else if (selectedGoals.length < 3) {
      // Add goal with default weight
      const defaultWeight = selectedGoals.length === 0 ? 5 : 
                           selectedGoals.length === 1 ? 3 : 
                           Math.max(0, remainingWeight)
      setSelectedGoals(prev => [...prev, { goal, weight: defaultWeight }])
    }
  }

  const updateWeight = (goal: Goal, weight: number) => {
    setSelectedGoals(prev =>
      prev.map(g => (g.goal === goal ? { ...g, weight: Math.max(0, Math.min(10, weight)) } : g))
    )
  }

  const getGoalInfo = (goal: Goal) => GOALS.find(g => g.value === goal)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-2">
        <label className="block text-sm font-medium text-secondary-700">
          Select 3 Goals (weights must sum to 10)
        </label>
        <span className={clsx(
          'text-sm font-medium px-2 py-1 rounded',
          totalWeight === 10 ? 'bg-success-100 text-success-700' : 
          totalWeight > 10 ? 'bg-destructive-100 text-destructive-700' :
          'bg-accent-100 text-accent-700'
        )}>
          {totalWeight}/10
        </span>
      </div>

      {/* Goal selection grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
        {GOALS.map((goal) => {
          const selected = isGoalSelected(goal.value as Goal)
          const disabled = !selected && selectedGoals.length >= 3

          return (
            <button
              key={goal.value}
              type="button"
              onClick={() => toggleGoal(goal.value as Goal)}
              disabled={disabled}
              className={clsx(
                'p-3 rounded-lg border-2 text-left transition-all',
                selected
                  ? 'border-primary-500 bg-primary-50'
                  : disabled
                  ? 'border-secondary-200 bg-secondary-50 opacity-50 cursor-not-allowed'
                  : 'border-secondary-200 hover:border-secondary-300 hover:bg-secondary-50'
              )}
            >
              <div className="font-medium text-sm">{goal.label}</div>
              <div className="text-xs text-secondary-500">{goal.description}</div>
            </button>
          )
        })}
      </div>

      {/* Weight allocation */}
      {selectedGoals.length > 0 && (
        <div className="mt-4 space-y-3 p-4 bg-secondary-50 rounded-lg">
          <div className="text-sm font-medium text-secondary-700 mb-2">
            Allocate Weights
          </div>
          {selectedGoals.map((goalWeight) => {
            const info = getGoalInfo(goalWeight.goal)
            return (
              <div key={goalWeight.goal} className="flex items-center gap-4">
                <div className="flex-1">
                  <div className="text-sm font-medium">{info?.label}</div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => updateWeight(goalWeight.goal, goalWeight.weight - 1)}
                    className="w-8 h-8 rounded-full bg-secondary-200 hover:bg-secondary-300 flex items-center justify-center text-secondary-700"
                  >
                    -
                  </button>
                  <span className="w-8 text-center font-mono font-bold text-lg">
                    {goalWeight.weight}
                  </span>
                  <button
                    type="button"
                    onClick={() => updateWeight(goalWeight.goal, goalWeight.weight + 1)}
                    className="w-8 h-8 rounded-full bg-secondary-200 hover:bg-secondary-300 flex items-center justify-center text-secondary-700"
                  >
                    +
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Validation message */}
      {selectedGoals.length < 3 && (
        <p className="text-sm text-secondary-500">
          Select {3 - selectedGoals.length} more goal{3 - selectedGoals.length > 1 ? 's' : ''}
        </p>
      )}

      {error && (
        <p className="text-sm text-destructive-600">{error}</p>
      )}
    </div>
  )
}

export default GoalSelector

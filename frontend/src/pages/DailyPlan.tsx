import React, { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate, Link } from '@tanstack/react-router'
import { Card, Button, Alert, Spinner, Skeleton } from '../components/common'
import SessionDetails from '../components/features/daily/SessionDetails'
import StreamingFeedback from '../components/features/daily/StreamingFeedback'
import AdaptationForm from '../components/features/daily/AdaptationForm'
import { dailyApi, formatDateForApi, getTodayForApi } from '../api/daily'
import { programsApi } from '../api/programs'
import useSse from '../hooks/useSse'
import type { DailyPlanResponse, ProgramResponse, AdaptationRequest, SessionResponse } from '../types/api'
import {
  CalendarIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  SparklesIcon,
  CheckCircleIcon,
  SunIcon,
} from '@heroicons/react/24/outline'

type ViewMode = 'planned' | 'adapted'

const DailyPlan: React.FC = () => {
  const navigate = useNavigate()
  // Try to get date from URL params (for /daily/$date route)
  const params = useParams({ strict: false }) as { date?: string }

  // Date navigation - initialize from URL param or today
  const getInitialDate = () => {
    if (params.date && /^\d{4}-\d{2}-\d{2}$/.test(params.date)) {
      return new Date(params.date + 'T00:00:00')
    }
    return new Date()
  }

  const [selectedDate, setSelectedDate] = useState(getInitialDate)
  const dateString = formatDateForApi(selectedDate)
  const isToday = dateString === getTodayForApi()

  // Program state
  const [programs, setPrograms] = useState<ProgramResponse[]>([])
  const [activeProgram, setActiveProgram] = useState<ProgramResponse | null>(null)
  const [loadingPrograms, setLoadingPrograms] = useState(true)

  // Plan state
  const [dailyPlan, setDailyPlan] = useState<DailyPlanResponse | null>(null)
  const [loadingPlan, setLoadingPlan] = useState(false)
  const [planError, setPlanError] = useState<string | null>(null)

  // View mode
  const [viewMode, setViewMode] = useState<ViewMode>('planned')
  const [adaptedSession, setAdaptedSession] = useState<SessionResponse | null>(null)
  const [showAdaptForm, setShowAdaptForm] = useState(false)

  // SSE streaming for adaptation
  const {
    content: streamContent,
    recoveryScore,
    threadId,
    isStreaming,
    error: streamError,
    start: startStream,
    reset: resetStream,
  } = useSse()

  // Fetch programs on mount
  useEffect(() => {
    const fetchPrograms = async () => {
      try {
        const allPrograms = await programsApi.list({ active_only: true })
        setPrograms(allPrograms)
        if (allPrograms.length > 0) {
          setActiveProgram(allPrograms[0])
        }
      } catch (err) {
        console.error('Failed to fetch programs:', err)
      } finally {
        setLoadingPrograms(false)
      }
    }
    fetchPrograms()
  }, [])

  // Fetch daily plan when date or program changes
  useEffect(() => {
    if (!activeProgram) return

    const fetchDailyPlan = async () => {
      setLoadingPlan(true)
      setPlanError(null)
      setDailyPlan(null)
      setAdaptedSession(null)
      setViewMode('planned')
      resetStream()

      try {
        const plan = await dailyApi.getPlan(dateString, activeProgram.id)
        setDailyPlan(plan)
      } catch (err: any) {
        setPlanError(err?.message || 'Failed to load daily plan')
      } finally {
        setLoadingPlan(false)
      }
    }

    fetchDailyPlan()
  }, [dateString, activeProgram, resetStream])

  // Date navigation handlers - update URL when navigating
  const goToPreviousDay = () => {
    const newDate = new Date(selectedDate)
    newDate.setDate(newDate.getDate() - 1)
    const newDateStr = formatDateForApi(newDate)
    setSelectedDate(newDate)
    navigate({ to: '/daily/$date', params: { date: newDateStr } })
  }

  const goToNextDay = () => {
    const newDate = new Date(selectedDate)
    newDate.setDate(newDate.getDate() + 1)
    const newDateStr = formatDateForApi(newDate)
    setSelectedDate(newDate)
    navigate({ to: '/daily/$date', params: { date: newDateStr } })
  }

  const goToToday = () => {
    setSelectedDate(new Date())
    navigate({ to: '/daily' })
  }

  // Adaptation handler
  const handleAdapt = useCallback(
    async (request: AdaptationRequest) => {
      setShowAdaptForm(false)
      setViewMode('adapted')
      await startStream(`/days/${dateString}/adapt/stream`, request)
    },
    [dateString, startStream]
  )

  // Accept adapted plan
  const handleAcceptPlan = async () => {
    if (!threadId) return

    try {
      const result = await dailyApi.acceptPlan({ thread_id: threadId })
      if (result.success) {
        // Refresh the daily plan
        if (activeProgram) {
          const plan = await dailyApi.getPlan(dateString, activeProgram.id)
          setDailyPlan(plan)
        }
      }
    } catch (err: any) {
      console.error('Failed to accept plan:', err)
    }
  }

  // Format date for display
  const formatDateDisplay = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      weekday: 'long',
      month: 'short',
      day: 'numeric',
    })
  }

  // Loading state
  if (loadingPrograms) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  // No programs
  if (!activeProgram) {
    return (
      <Card>
        <div className="text-center py-12">
          <SparklesIcon className="w-12 h-12 mx-auto text-secondary-300 mb-4" />
          <h2 className="text-xl font-semibold text-secondary-900 mb-2">
            No Active Program
          </h2>
          <p className="text-secondary-600 mb-6">
            Create a training program to see your daily workout plan.
          </p>
          <Link to="/onboarding">
            <Button>Create Program</Button>
          </Link>
        </div>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Date Navigation Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" onClick={goToPreviousDay}>
            <ChevronLeftIcon className="w-5 h-5" />
          </Button>

          <div className="flex items-center gap-2 px-4 py-2">
            <CalendarIcon className="w-5 h-5 text-secondary-500" />
            <span className="text-lg font-semibold text-secondary-900">
              {formatDateDisplay(selectedDate)}
            </span>
            {isToday && (
              <span className="text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full">
                Today
              </span>
            )}
          </div>

          <Button variant="ghost" size="sm" onClick={goToNextDay}>
            <ChevronRightIcon className="w-5 h-5" />
          </Button>
        </div>

        {!isToday && (
          <Button variant="secondary" size="sm" onClick={goToToday}>
            <SunIcon className="w-4 h-4 mr-1" />
            Today
          </Button>
        )}
      </div>

      {/* Program Selector (if multiple programs) */}
      {programs.length > 1 && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-secondary-600">Program:</span>
          <select
            className="px-3 py-1.5 text-sm border border-secondary-300 rounded-input focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
            value={activeProgram.id}
            onChange={e => {
              const program = programs.find(p => p.id === parseInt(e.target.value))
              if (program) setActiveProgram(program)
            }}
          >
            {programs.map(p => (
              <option key={p.id} value={p.id}>
                {p.split_template} - {p.goal_1}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Loading state for plan */}
      {loadingPlan && (
        <Card>
          <div className="flex items-center justify-center py-12">
            <Spinner size="lg" />
          </div>
        </Card>
      )}

      {/* Error state */}
      {planError && (
        <Alert variant="error">
          {planError}
        </Alert>
      )}

      {/* Daily plan content */}
      {dailyPlan && !loadingPlan && (
        <>
          {/* Rest Day */}
          {dailyPlan.is_rest_day ? (
            <Card>
              <div className="text-center py-12">
                <SunIcon className="w-16 h-16 mx-auto text-accent-400 mb-4" />
                <h2 className="text-2xl font-bold text-secondary-900 mb-2">
                  Rest Day
                </h2>
                {dailyPlan.coach_message && (
                  <p className="text-secondary-600 max-w-md mx-auto">
                    {dailyPlan.coach_message}
                  </p>
                )}
                {dailyPlan.recommended_activities && dailyPlan.recommended_activities.length > 0 && (
                  <div className="mt-6">
                    <p className="text-sm text-secondary-500 mb-2">
                      Recommended activities:
                    </p>
                    <div className="flex flex-wrap justify-center gap-2">
                      {dailyPlan.recommended_activities.map((activity, i) => (
                        <span
                          key={i}
                          className="px-3 py-1 bg-accent-50 text-accent-700 rounded-full text-sm"
                        >
                          {activity}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Card>
          ) : (
            <>
              {/* View Mode Toggle */}
              {(streamContent || adaptedSession) && (
                <div className="flex gap-2">
                  <Button
                    variant={viewMode === 'planned' ? 'primary' : 'secondary'}
                    size="sm"
                    onClick={() => setViewMode('planned')}
                  >
                    Planned Session
                  </Button>
                  <Button
                    variant={viewMode === 'adapted' ? 'primary' : 'secondary'}
                    size="sm"
                    onClick={() => setViewMode('adapted')}
                  >
                    Adapted Session
                  </Button>
                </div>
              )}

              {/* Main Content Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Session Details */}
                <div className="lg:col-span-2">
                  <Card>
                    <div className="p-6">
                      {viewMode === 'planned' && dailyPlan.session ? (
                        <SessionDetails session={dailyPlan.session} />
                      ) : viewMode === 'adapted' ? (
                        <StreamingFeedback
                          content={streamContent}
                          recoveryScore={recoveryScore}
                          isStreaming={isStreaming}
                          error={streamError?.message}
                        />
                      ) : (
                        <div className="text-center py-8 text-secondary-500">
                          No session data available
                        </div>
                      )}
                    </div>
                  </Card>
                </div>

                {/* Sidebar - Adaptation Controls */}
                <div className="space-y-4">
                  {/* Adapt Session Card */}
                  <Card>
                    <div className="p-4">
                      <div className="flex items-center gap-2 mb-4">
                        <SparklesIcon className="w-5 h-5 text-primary-500" />
                        <h3 className="font-semibold text-secondary-900">
                          Adapt Session
                        </h3>
                      </div>

                      {showAdaptForm ? (
                        <>
                          <AdaptationForm
                            programId={activeProgram.id}
                            onSubmit={handleAdapt}
                            isLoading={isStreaming}
                          />
                          <Button
                            variant="ghost"
                            size="sm"
                            fullWidth
                            onClick={() => setShowAdaptForm(false)}
                            className="mt-2"
                          >
                            Cancel
                          </Button>
                        </>
                      ) : (
                        <Button
                          fullWidth
                          onClick={() => setShowAdaptForm(true)}
                          disabled={isStreaming}
                        >
                          <SparklesIcon className="w-4 h-4 mr-2" />
                          Customize Today's Workout
                        </Button>
                      )}
                    </div>
                  </Card>

                  {/* Accept Plan Button (when adapted) */}
                  {threadId && !isStreaming && viewMode === 'adapted' && (
                    <Card>
                      <div className="p-4">
                        <Button
                          variant="primary"
                          fullWidth
                          onClick={handleAcceptPlan}
                        >
                          <CheckCircleIcon className="w-4 h-4 mr-2" />
                          Accept Adapted Plan
                        </Button>
                        <p className="text-xs text-secondary-500 text-center mt-2">
                          Save this adapted session to your plan
                        </p>
                      </div>
                    </Card>
                  )}

                  {/* Quick Stats Card */}
                  {dailyPlan.session && (
                    <Card>
                      <div className="p-4">
                        <h4 className="text-sm font-medium text-secondary-700 mb-3">
                          Session Overview
                        </h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-secondary-500">Type</span>
                            <span className="font-medium capitalize">
                              {dailyPlan.session.session_type.replace('_', ' ')}
                            </span>
                          </div>
                          {dailyPlan.session.estimated_duration_minutes && (
                            <div className="flex justify-between">
                              <span className="text-secondary-500">Duration</span>
                              <span className="font-medium">
                                {dailyPlan.session.estimated_duration_minutes} min
                              </span>
                            </div>
                          )}
                          {dailyPlan.session.main && (
                            <div className="flex justify-between">
                              <span className="text-secondary-500">Main Exercises</span>
                              <span className="font-medium">
                                {dailyPlan.session.main.length}
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </Card>
                  )}
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}

export default DailyPlan

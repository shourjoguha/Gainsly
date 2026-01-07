import React, { useState, useEffect } from 'react'
import { Link } from '@tanstack/react-router'
import { Button, Alert, Spinner, Card, CardContent } from '../components/common'
import ProgramCard from '../components/features/program/ProgramCard'
import { programsApi } from '../api/programs'
import type { ProgramResponse } from '../types/api'
import { PlusIcon, DocumentTextIcon } from '@heroicons/react/24/outline'

const Programs: React.FC = () => {
  const [programs, setPrograms] = useState<ProgramResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | 'active'>('all')

  useEffect(() => {
    const fetchPrograms = async () => {
      try {
        const data = await programsApi.list({ active_only: filter === 'active' })
        setPrograms(data)
      } catch (err: any) {
        setError(err.message || 'Failed to load programs')
      } finally {
        setLoading(false)
      }
    }
    fetchPrograms()
  }, [filter])

  const activePrograms = programs.filter(p => p.is_active)
  const inactivePrograms = programs.filter(p => !p.is_active)

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-secondary-900">Programs</h1>
          <p className="text-secondary-600">
            Your training programs and history.
          </p>
        </div>
        <Link to="/onboarding">
          <Button leftIcon={<PlusIcon className="w-4 h-4" />}>
            New Program
          </Button>
        </Link>
      </div>

      {error && (
        <Alert variant="error" dismissible onDismiss={() => setError(null)} className="mb-6">
          {error}
        </Alert>
      )}

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6">
        <Button
          variant={filter === 'all' ? 'primary' : 'secondary'}
          size="sm"
          onClick={() => setFilter('all')}
        >
          All ({programs.length})
        </Button>
        <Button
          variant={filter === 'active' ? 'primary' : 'secondary'}
          size="sm"
          onClick={() => setFilter('active')}
        >
          Active ({activePrograms.length})
        </Button>
      </div>

      {/* No Programs */}
      {programs.length === 0 && (
        <Card>
          <CardContent>
            <div className="text-center py-12">
              <DocumentTextIcon className="w-12 h-12 mx-auto text-secondary-300 mb-4" />
              <h2 className="text-lg font-semibold text-secondary-900 mb-2">
                No Programs Yet
              </h2>
              <p className="text-secondary-600 mb-6">
                Create your first training program to get started.
              </p>
              <Link to="/onboarding">
                <Button leftIcon={<PlusIcon className="w-4 h-4" />}>
                  Create Program
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Active Programs */}
      {activePrograms.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-secondary-900 mb-4">
            Active Programs
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            {activePrograms.map(program => (
              <ProgramCard key={program.id} program={program} />
            ))}
          </div>
        </div>
      )}

      {/* Inactive/Past Programs */}
      {filter === 'all' && inactivePrograms.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-secondary-900 mb-4">
            Past Programs
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            {inactivePrograms.map(program => (
              <ProgramCard key={program.id} program={program} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Programs

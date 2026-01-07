import React, { useState } from 'react'
import { clsx } from 'clsx'
import { Card, CardContent } from '../components/common'
import { WorkoutLogForm, SorenessLogger, RecoveryLogger } from '../components/features/logging'
import {
  ClipboardDocumentCheckIcon,
  HeartIcon,
  BoltIcon,
} from '@heroicons/react/24/outline'

type LogType = 'workout' | 'soreness' | 'recovery'

const TABS: { key: LogType; label: string; icon: React.ReactNode }[] = [
  { key: 'workout', label: 'Workout', icon: <ClipboardDocumentCheckIcon className="w-5 h-5" /> },
  { key: 'soreness', label: 'Soreness', icon: <BoltIcon className="w-5 h-5" /> },
  { key: 'recovery', label: 'Recovery', icon: <HeartIcon className="w-5 h-5" /> },
]

const Logging: React.FC = () => {
  const [activeTab, setActiveTab] = useState<LogType>('workout')

  const handleSuccess = () => {
    // Could navigate elsewhere or show a toast
    // For now, just stay on the page
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold text-secondary-900 mb-2">Log Your Progress</h1>
      <p className="text-secondary-600 mb-6">
        Track your workouts, soreness, and recovery to help optimize your training.
      </p>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={clsx(
              'flex items-center gap-2 px-4 py-2 rounded-btn text-sm font-medium transition-all',
              activeTab === tab.key
                ? 'bg-primary-500 text-white'
                : 'bg-secondary-100 text-secondary-600 hover:bg-secondary-200'
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <Card>
        <CardContent>
          {activeTab === 'workout' && (
            <WorkoutLogForm onSuccess={handleSuccess} />
          )}
          {activeTab === 'soreness' && (
            <SorenessLogger onSuccess={handleSuccess} />
          )}
          {activeTab === 'recovery' && (
            <RecoveryLogger onSuccess={handleSuccess} />
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default Logging

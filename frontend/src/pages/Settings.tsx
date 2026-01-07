import React, { useState } from 'react'
import { clsx } from 'clsx'
import { UserPreferences, MovementRules } from '../components/features/settings'
import {
  UserCircleIcon,
  AdjustmentsHorizontalIcon,
} from '@heroicons/react/24/outline'

type SettingsTab = 'preferences' | 'movements'

const TABS: { key: SettingsTab; label: string; icon: React.ReactNode }[] = [
  { key: 'preferences', label: 'Preferences', icon: <UserCircleIcon className="w-5 h-5" /> },
  { key: 'movements', label: 'Movement Rules', icon: <AdjustmentsHorizontalIcon className="w-5 h-5" /> },
]

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('preferences')

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-secondary-900 mb-2">Settings</h1>
      <p className="text-secondary-600 mb-6">
        Customize your training experience and preferences.
      </p>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-secondary-200">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={clsx(
              'flex items-center gap-2 px-4 py-3 text-sm font-medium transition-all border-b-2 -mb-px',
              activeTab === tab.key
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-secondary-600 hover:text-secondary-900 hover:border-secondary-300'
            )}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'preferences' && <UserPreferences />}
        {activeTab === 'movements' && <MovementRules />}
      </div>
    </div>
  )
}

export default Settings

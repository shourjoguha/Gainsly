import React, { useState, useEffect } from 'react'
import { Button, Input, Select, Alert, Card, CardContent, Spinner } from '../../common'
import { settingsApi } from '../../../api/settings'
import {
  E1RM_FORMULAS,
  PERSONA_TONES,
  PERSONA_AGGRESSION,
} from '../../../utils/constants'
import type { UserSettingsResponse, UserProfileResponse } from '../../../types/api'
import { CheckCircleIcon } from '@heroicons/react/24/outline'

const UserPreferences: React.FC = () => {
  const [, setSettings] = useState<UserSettingsResponse | null>(null)
  const [, setProfile] = useState<UserProfileResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  // Form state
  const [formData, setFormData] = useState({
    // Settings
    e1rm_formula: '',
    use_metric: true,
    default_session_duration_minutes: '',
    // Profile
    name: '',
    experience_level: '',
    persona_tone: '',
    persona_aggression: '',
  })

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [settingsData, profileData] = await Promise.all([
          settingsApi.getSettings(),
          settingsApi.getProfile(),
        ])
        setSettings(settingsData)
        setProfile(profileData)

        // Initialize form
        setFormData({
          e1rm_formula: settingsData.active_e1rm_formula || settingsData.e1rm_formula || 'epley',
          use_metric: settingsData.use_metric ?? true,
          default_session_duration_minutes: String(settingsData.default_session_duration_minutes || 60),
          name: profileData.name || '',
          experience_level: profileData.experience_level || 'intermediate',
          persona_tone: profileData.persona_tone || 'neutral',
          persona_aggression: profileData.persona_aggression || 'balanced',
        })
      } catch (err: any) {
        setError(err.message || 'Failed to load settings')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(false)
    setSaving(true)

    try {
      // Update settings
      await settingsApi.updateSettings({
        active_e1rm_formula: formData.e1rm_formula as any,
        use_metric: formData.use_metric,
        default_session_duration_minutes: parseInt(formData.default_session_duration_minutes) || 60,
      })

      // Update profile
      await settingsApi.updateProfile({
        name: formData.name || undefined,
        experience_level: formData.experience_level as any,
        persona_tone: formData.persona_tone as any,
        persona_aggression: formData.persona_aggression as any,
      })

      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    } catch (err: any) {
      setError(err.message || 'Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {error && (
        <Alert variant="error" dismissible onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert variant="success">
          <div className="flex items-center gap-2">
            <CheckCircleIcon className="w-5 h-5" />
            Settings saved successfully!
          </div>
        </Alert>
      )}

      {/* Profile Section */}
      <Card>
        <CardContent>
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Profile</h3>
          
          <div className="space-y-4">
            <Input
              label="Display Name"
              value={formData.name}
              onChange={e => setFormData(prev => ({ ...prev, name: e.target.value }))}
              placeholder="Your name"
            />

            <Select
              label="Experience Level"
              options={[
                { value: 'beginner', label: 'Beginner (< 1 year)' },
                { value: 'intermediate', label: 'Intermediate (1-3 years)' },
                { value: 'advanced', label: 'Advanced (3-5 years)' },
                { value: 'elite', label: 'Elite (5+ years)' },
              ]}
              value={formData.experience_level}
              onChange={e => setFormData(prev => ({ ...prev, experience_level: e.target.value }))}
            />
          </div>
        </CardContent>
      </Card>

      {/* Coach Persona Section */}
      <Card>
        <CardContent>
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Coach Persona</h3>
          <p className="text-sm text-secondary-600 mb-4">
            Customize how your AI coach communicates with you.
          </p>
          
          <div className="space-y-4">
            <Select
              label="Coaching Tone"
              options={PERSONA_TONES.map(t => ({ value: t.value, label: `${t.label} - ${t.description}` }))}
              value={formData.persona_tone}
              onChange={e => setFormData(prev => ({ ...prev, persona_tone: e.target.value }))}
            />

            <Select
              label="Training Aggressiveness"
              options={PERSONA_AGGRESSION.map(a => ({ value: a.value, label: `${a.label} - ${a.description}` }))}
              value={formData.persona_aggression}
              onChange={e => setFormData(prev => ({ ...prev, persona_aggression: e.target.value }))}
              helpText="How hard the coach pushes you"
            />
          </div>
        </CardContent>
      </Card>

      {/* Calculation Settings */}
      <Card>
        <CardContent>
          <h3 className="text-lg font-semibold text-secondary-900 mb-4">Calculation Preferences</h3>
          
          <div className="space-y-4">
            <Select
              label="e1RM Formula"
              options={E1RM_FORMULAS.map(f => ({ value: f.value, label: `${f.label} - ${f.description}` }))}
              value={formData.e1rm_formula}
              onChange={e => setFormData(prev => ({ ...prev, e1rm_formula: e.target.value }))}
              helpText="Formula for estimating one-rep max from submaximal loads"
            />

            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="use_metric"
                checked={formData.use_metric}
                onChange={e => setFormData(prev => ({ ...prev, use_metric: e.target.checked }))}
                className="w-4 h-4 text-primary-600 border-secondary-300 rounded focus:ring-primary-500"
              />
              <label htmlFor="use_metric" className="text-sm text-secondary-700">
                Use metric units (kg) instead of imperial (lbs)
              </label>
            </div>

            <Input
              label="Default Session Duration"
              type="number"
              min="15"
              max="180"
              value={formData.default_session_duration_minutes}
              onChange={e => setFormData(prev => ({ ...prev, default_session_duration_minutes: e.target.value }))}
              helpText="Target duration for sessions in minutes"
            />
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button type="submit" loading={saving}>
          Save Preferences
        </Button>
      </div>
    </form>
  )
}

export default UserPreferences

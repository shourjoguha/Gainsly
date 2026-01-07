import React, { useState, useEffect } from 'react'
import { clsx } from 'clsx'
import { Button, Select, Alert, Card, CardContent, Spinner, Modal } from '../../common'
import { settingsApi } from '../../../api/settings'
import type { MovementRuleResponse, MovementResponse } from '../../../types/api'
import { PlusIcon, TrashIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'

const RULE_TYPES = [
  { value: 'hard_no', label: 'Exclude', description: 'Never include this movement' },
  { value: 'hard_yes', label: 'Always Include', description: 'Prioritize this movement' },
  { value: 'preferred', label: 'Preferred', description: 'Prefer when appropriate' },
]

const CADENCE_OPTIONS = [
  { value: '', label: 'No specific cadence' },
  { value: 'per_microcycle', label: 'Per microcycle' },
  { value: 'weekly', label: 'Weekly' },
  { value: 'biweekly', label: 'Every 2 weeks' },
]

const MovementRules: React.FC = () => {
  const [rules, setRules] = useState<MovementRuleResponse[]>([])
  const [movements, setMovements] = useState<MovementResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Modal state
  const [showAddModal, setShowAddModal] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<MovementResponse[]>([])
  const [selectedMovement, setSelectedMovement] = useState<MovementResponse | null>(null)
  const [newRule, setNewRule] = useState({
    rule_type: 'hard_no',
    cadence: '',
    notes: '',
  })
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState<number | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [rulesData, movementsData] = await Promise.all([
          settingsApi.listMovementRules(),
          settingsApi.listMovements({ limit: 100 }),
        ])
        setRules(rulesData)
        setMovements(movementsData.movements)
      } catch (err: any) {
        setError(err.message || 'Failed to load movement rules')
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  // Search movements
  useEffect(() => {
    if (searchQuery.length < 2) {
      setSearchResults([])
      return
    }

    const filtered = movements.filter(m =>
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.pattern?.toLowerCase().includes(searchQuery.toLowerCase())
    )
    setSearchResults(filtered.slice(0, 10))
  }, [searchQuery, movements])

  const handleAddRule = async () => {
    if (!selectedMovement) return

    setSaving(true)
    setError(null)

    try {
      const newRuleData = await settingsApi.createMovementRule({
        movement_id: selectedMovement.id,
        rule_type: newRule.rule_type as 'hard_no' | 'hard_yes' | 'preferred',
        cadence: newRule.cadence as any || undefined,
        notes: newRule.notes || undefined,
      })

      setRules(prev => [...prev, newRuleData])
      setShowAddModal(false)
      resetForm()
    } catch (err: any) {
      setError(err.message || 'Failed to add rule')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteRule = async (ruleId: number) => {
    setDeleting(ruleId)
    setError(null)

    try {
      await settingsApi.deleteMovementRule(ruleId)
      setRules(prev => prev.filter(r => r.id !== ruleId))
    } catch (err: any) {
      setError(err.message || 'Failed to delete rule')
    } finally {
      setDeleting(null)
    }
  }

  const resetForm = () => {
    setSelectedMovement(null)
    setSearchQuery('')
    setSearchResults([])
    setNewRule({ rule_type: 'hard_no', cadence: '', notes: '' })
  }

  const getRuleColor = (ruleType: string) => {
    switch (ruleType) {
      case 'hard_no':
        return 'bg-destructive-50 border-destructive-200 text-destructive-700'
      case 'hard_yes':
        return 'bg-success-50 border-success-200 text-success-700'
      case 'preferred':
        return 'bg-primary-50 border-primary-200 text-primary-700'
      default:
        return 'bg-secondary-50 border-secondary-200 text-secondary-700'
    }
  }

  const getRuleLabel = (ruleType: string) => {
    return RULE_TYPES.find(r => r.value === ruleType)?.label || ruleType
  }

  if (loading) {
    return (
      <div className="flex justify-center py-12">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="error" dismissible onDismiss={() => setError(null)}>
          {error}
        </Alert>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-secondary-900">Movement Rules</h3>
          <p className="text-sm text-secondary-600">
            Customize which movements to include or exclude from your programs.
          </p>
        </div>
        <Button onClick={() => setShowAddModal(true)} leftIcon={<PlusIcon className="w-4 h-4" />}>
          Add Rule
        </Button>
      </div>

      {/* Rules List */}
      {rules.length === 0 ? (
        <Card>
          <CardContent>
            <div className="text-center py-8 text-secondary-500">
              No movement rules configured yet.
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {rules.map(rule => (
            <Card key={rule.id}>
              <CardContent>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <span className={clsx(
                      'px-2 py-1 text-xs font-medium rounded border',
                      getRuleColor(rule.rule_type)
                    )}>
                      {getRuleLabel(rule.rule_type)}
                    </span>
                    <div>
                      <div className="font-medium text-secondary-900">
                        {rule.movement_name || `Movement #${rule.movement_id}`}
                      </div>
                      {rule.cadence && (
                        <div className="text-xs text-secondary-500">
                          Cadence: {rule.cadence}
                        </div>
                      )}
                      {rule.notes && (
                        <div className="text-xs text-secondary-500 mt-1">
                          {rule.notes}
                        </div>
                      )}
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDeleteRule(rule.id)}
                    loading={deleting === rule.id}
                    className="text-destructive-500 hover:text-destructive-600"
                  >
                    <TrashIcon className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Add Rule Modal */}
      <Modal
        isOpen={showAddModal}
        onClose={() => { setShowAddModal(false); resetForm() }}
        title="Add Movement Rule"
      >
        <div className="space-y-4">
          {/* Movement Search */}
          <div>
            <label className="block text-xs font-medium text-secondary-700 mb-1">
              Search Movement
            </label>
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-secondary-400" />
              <input
                type="text"
                className="w-full pl-10 pr-3 py-2 text-sm border border-secondary-300 rounded-input focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                placeholder="Search by name or pattern..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && !selectedMovement && (
              <div className="mt-2 border border-secondary-200 rounded-lg max-h-48 overflow-y-auto">
                {searchResults.map(m => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => {
                      setSelectedMovement(m)
                      setSearchQuery(m.name)
                      setSearchResults([])
                    }}
                    className="w-full px-3 py-2 text-left text-sm hover:bg-secondary-50 border-b border-secondary-100 last:border-b-0"
                  >
                    <div className="font-medium">{m.name}</div>
                    {m.pattern && (
                      <div className="text-xs text-secondary-500">{m.pattern}</div>
                    )}
                  </button>
                ))}
              </div>
            )}

            {/* Selected Movement */}
            {selectedMovement && (
              <div className="mt-2 p-3 bg-primary-50 border border-primary-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-primary-900">{selectedMovement.name}</div>
                    {selectedMovement.pattern && (
                      <div className="text-xs text-primary-700">{selectedMovement.pattern}</div>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelectedMovement(null)
                      setSearchQuery('')
                    }}
                  >
                    Change
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Rule Type */}
          <Select
            label="Rule Type"
            options={RULE_TYPES.map(r => ({ value: r.value, label: `${r.label} - ${r.description}` }))}
            value={newRule.rule_type}
            onChange={e => setNewRule(prev => ({ ...prev, rule_type: e.target.value }))}
          />

          {/* Cadence (for hard_yes and preferred) */}
          {newRule.rule_type !== 'hard_no' && (
            <Select
              label="Cadence (Optional)"
              options={CADENCE_OPTIONS}
              value={newRule.cadence}
              onChange={e => setNewRule(prev => ({ ...prev, cadence: e.target.value }))}
              helpText="How often to include this movement"
            />
          )}

          {/* Notes */}
          <div>
            <label className="block text-xs font-medium text-secondary-700 mb-1">
              Notes (Optional)
            </label>
            <textarea
              value={newRule.notes}
              onChange={e => setNewRule(prev => ({ ...prev, notes: e.target.value }))}
              placeholder="Why this rule? Any specific context..."
              rows={2}
              className="w-full px-3 py-2 text-sm border border-secondary-300 rounded-input focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
            />
          </div>

          {/* Actions */}
          <div className="flex gap-3 pt-4 border-t border-secondary-200">
            <Button
              variant="secondary"
              onClick={() => { setShowAddModal(false); resetForm() }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleAddRule}
              loading={saving}
              disabled={!selectedMovement}
              fullWidth
            >
              Add Rule
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default MovementRules

import { useState } from 'react';
import { MovementRuleType } from '@/types';
import { useProgramWizardStore } from '@/stores/program-wizard-store';
import { useMovements } from '@/api/settings';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { Search, ThumbsUp, ThumbsDown, X } from 'lucide-react';

export function MovementsStep() {
  const { movementRules, addMovementRule, removeMovementRule } = useProgramWizardStore();
  const [search, setSearch] = useState('');
  const { data: movementsData, isLoading } = useMovements({ search, limit: 20 });

  const movements = movementsData?.movements ?? [];
  
  const getRule = (movementId: number) => {
    return movementRules.find((r) => r.movement_id === movementId);
  };

  const handleSetRule = (movementId: number, ruleType: MovementRuleType) => {
    const existing = getRule(movementId);
    if (existing?.rule_type === ruleType) {
      removeMovementRule(movementId);
    } else {
      addMovementRule({ movement_id: movementId, rule_type: ruleType });
    }
  };

  const hardNos = movementRules.filter((r) => r.rule_type === MovementRuleType.HARD_NO);
  const hardYes = movementRules.filter((r) => r.rule_type === MovementRuleType.HARD_YES);
  const preferred = movementRules.filter((r) => r.rule_type === MovementRuleType.PREFERRED);

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-xl font-bold">Movement Preferences</h2>
        <p className="text-foreground-muted text-sm">
          Any exercises you love or want to avoid? This is optional.
        </p>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-foreground-muted" />
        <input
          type="text"
          placeholder="Search movements..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full h-10 pl-10 pr-4 rounded-lg bg-background-elevated border border-border focus:border-accent focus:outline-none text-sm"
        />
      </div>

      {/* Current rules summary */}
      {movementRules.length > 0 && (
        <div className="bg-background-elevated rounded-lg p-4 space-y-3">
          <p className="text-sm font-medium">Your preferences:</p>
          
          {hardYes.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {hardYes.map((rule) => (
                <span
                  key={rule.movement_id}
                  className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-cta/20 text-cta"
                >
                  <ThumbsUp className="h-3 w-3" />
                  Movement #{rule.movement_id}
                  <button onClick={() => removeMovementRule(rule.movement_id)}>
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
          
          {preferred.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {preferred.map((rule) => (
                <span
                  key={rule.movement_id}
                  className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-accent/20 text-accent"
                >
                  ★ Movement #{rule.movement_id}
                  <button onClick={() => removeMovementRule(rule.movement_id)}>
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
          
          {hardNos.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {hardNos.map((rule) => (
                <span
                  key={rule.movement_id}
                  className="inline-flex items-center gap-1 text-xs px-2 py-1 rounded-full bg-error/20 text-error"
                >
                  <ThumbsDown className="h-3 w-3" />
                  Movement #{rule.movement_id}
                  <button onClick={() => removeMovementRule(rule.movement_id)}>
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Movement list */}
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {isLoading ? (
          <div className="text-center py-8 text-foreground-muted">Loading movements...</div>
        ) : movements.length === 0 ? (
          <div className="text-center py-8 text-foreground-muted">
            {search ? 'No movements found' : 'Search for movements above'}
          </div>
        ) : (
          movements.map((movement) => {
            const rule = getRule(movement.id);
            return (
              <Card key={movement.id} className="p-3">
                <div className="flex items-center gap-3">
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-sm">{movement.name}</h4>
                    <p className="text-xs text-foreground-muted">
                      {movement.primary_pattern} • {movement.default_equipment ?? 'Any equipment'}
                    </p>
                  </div>
                  <div className="flex gap-1">
                    <button
                      onClick={() => handleSetRule(movement.id, MovementRuleType.HARD_YES)}
                      className={cn(
                        "h-8 w-8 rounded-lg flex items-center justify-center transition-colors",
                        rule?.rule_type === MovementRuleType.HARD_YES
                          ? "bg-cta text-background"
                          : "bg-background-elevated hover:bg-cta/20 text-foreground-muted"
                      )}
                      title="Must include"
                    >
                      <ThumbsUp className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleSetRule(movement.id, MovementRuleType.PREFERRED)}
                      className={cn(
                        "h-8 w-8 rounded-lg flex items-center justify-center transition-colors",
                        rule?.rule_type === MovementRuleType.PREFERRED
                          ? "bg-accent text-background"
                          : "bg-background-elevated hover:bg-accent/20 text-foreground-muted"
                      )}
                      title="Prefer"
                    >
                      ★
                    </button>
                    <button
                      onClick={() => handleSetRule(movement.id, MovementRuleType.HARD_NO)}
                      className={cn(
                        "h-8 w-8 rounded-lg flex items-center justify-center transition-colors",
                        rule?.rule_type === MovementRuleType.HARD_NO
                          ? "bg-error text-background"
                          : "bg-background-elevated hover:bg-error/20 text-foreground-muted"
                      )}
                      title="Never include"
                    >
                      <ThumbsDown className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </Card>
            );
          })
        )}
      </div>

      <p className="text-center text-xs text-foreground-subtle">
        💡 This is optional. Jerome will select appropriate exercises based on your goals.
      </p>
    </div>
  );
}

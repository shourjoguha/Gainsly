import { createFileRoute } from '@tanstack/react-router';
import { useState } from 'react';
import { Heart, Ban, Star, Search, Loader2, Filter } from 'lucide-react';
import { useMovements, useMovementRules, useCreateMovementRule, useDeleteMovementRule } from '@/api/settings';
import { MovementRuleType, MovementPattern } from '@/types';
import { useUIStore } from '@/stores/ui-store';
import { cn } from '@/lib/utils';

export const Route = createFileRoute('/favorites')({
  component: FavoritesPage,
});

function FavoritesPage() {
  const [search, setSearch] = useState('');
  const [selectedPattern, setSelectedPattern] = useState<MovementPattern | 'all'>('all');
  const { addToast } = useUIStore();
  
  const { data: movementsData, isLoading: isLoadingMovements } = useMovements({ limit: 200 });
  const { data: rules = [], isLoading: isLoadingRules } = useMovementRules();
  const createRule = useCreateMovementRule();
  const deleteRule = useDeleteMovementRule();
  
  const movements = movementsData?.movements || [];
  
  // Movement pattern options for filtering
  const patternOptions: { value: MovementPattern | 'all'; label: string }[] = [
    { value: 'all', label: 'All Patterns' },
    { value: MovementPattern.SQUAT, label: 'Squat' },
    { value: MovementPattern.HINGE, label: 'Hinge' },
    { value: MovementPattern.HORIZONTAL_PUSH, label: 'Horizontal Push' },
    { value: MovementPattern.VERTICAL_PUSH, label: 'Vertical Push' },
    { value: MovementPattern.HORIZONTAL_PULL, label: 'Horizontal Pull' },
    { value: MovementPattern.VERTICAL_PULL, label: 'Vertical Pull' },
    { value: MovementPattern.LUNGE, label: 'Lunge' },
    { value: MovementPattern.CARRY, label: 'Carry' },
    { value: MovementPattern.CORE, label: 'Core' },
    { value: MovementPattern.ROTATION, label: 'Rotation' },
    { value: MovementPattern.PLYOMETRIC, label: 'Plyometric' },
    { value: MovementPattern.OLYMPIC, label: 'Olympic' },
    { value: MovementPattern.ISOLATION, label: 'Isolation' },
    { value: MovementPattern.MOBILITY, label: 'Mobility' },
    { value: MovementPattern.ISOMETRIC, label: 'Isometric' },
  ];
  
  // Filter movements by search and pattern
  const filteredMovements = movements.filter((m) => {
    const matchesSearch = m.name.toLowerCase().includes(search.toLowerCase());
    const matchesPattern = selectedPattern === 'all' || m.primary_pattern === selectedPattern;
    return matchesSearch && matchesPattern;
  });
  
  // Get rule for a movement
  const getMovementRule = (movementId: number) => {
    return rules.find((r) => r.movement_id === movementId);
  };
  
  const handleToggleRule = async (movementId: number, ruleType: MovementRuleType) => {
    const existingRule = getMovementRule(movementId);
    
    try {
      if (existingRule) {
        if (existingRule.rule_type === ruleType) {
          // Remove the rule if clicking the same type
          await deleteRule.mutateAsync(existingRule.id);
          addToast({
            type: 'success',
            message: 'Preference removed',
          });
        } else {
          // Delete old rule and create new one
          await deleteRule.mutateAsync(existingRule.id);
          await createRule.mutateAsync({
            movement_id: movementId,
            rule_type: ruleType,
          });
          addToast({
            type: 'success',
            message: 'Preference updated',
          });
        }
      } else {
        // Create new rule
        await createRule.mutateAsync({
          movement_id: movementId,
          rule_type: ruleType,
        });
        addToast({
          type: 'success',
          message: 'Preference saved',
        });
      }
    } catch {
      addToast({
        type: 'error',
        message: 'Failed to update preference',
      });
    }
  };
  
  if (isLoadingMovements || isLoadingRules) {
    return (
      <div className="container-app flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-foreground-muted" />
      </div>
    );
  }
  
  return (
    <div className="container-app py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">Favorites</h1>
        <p className="mt-2 text-sm text-foreground-muted">
          Mark movements as favorite, preferred, or to avoid. Your preferences will be used when generating programs and sessions.
        </p>
      </div>
      
      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-foreground-muted" />
          <input
            type="text"
            placeholder="Search movements..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-border bg-background px-10 py-3 text-foreground placeholder:text-foreground-muted focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
          />
        </div>
        
        {/* Pattern Filter */}
        <div className="flex items-center gap-3">
          <Filter className="h-5 w-5 text-foreground-muted" />
          <div className="flex-1 overflow-x-auto">
            <div className="flex gap-2">
              {patternOptions.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setSelectedPattern(option.value)}
                  className={cn(
                    'whitespace-nowrap rounded-lg px-4 py-2 text-sm font-medium transition-colors',
                    selectedPattern === option.value
                      ? 'bg-accent text-background'
                      : 'bg-background-elevated text-foreground-muted hover:bg-background hover:text-foreground'
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
      
      {/* Results Count */}
      <div className="mb-4 text-sm text-foreground-muted">
        Showing {filteredMovements.length} of {movements.length} movements
      </div>
      
      {/* Legend */}
      <div className="mb-4 flex flex-wrap gap-4 rounded-lg border border-border bg-background-elevated p-4">
        <div className="flex items-center gap-2">
          <Heart className="h-4 w-4 text-red-500" />
          <span className="text-sm text-foreground-muted">Favorite (must include)</span>
        </div>
        <div className="flex items-center gap-2">
          <Star className="h-4 w-4 text-yellow-500" />
          <span className="text-sm text-foreground-muted">Preferred</span>
        </div>
        <div className="flex items-center gap-2">
          <Ban className="h-4 w-4 text-gray-500" />
          <span className="text-sm text-foreground-muted">Avoid</span>
        </div>
      </div>
      
      {/* Movements List */}
      <div className="space-y-2">
        {filteredMovements.length === 0 ? (
          <div className="rounded-lg border border-border bg-background-elevated p-8 text-center">
            <p className="text-foreground-muted">No movements found</p>
          </div>
        ) : (
          filteredMovements.map((movement) => {
            const rule = getMovementRule(movement.id);
            const ruleType = rule?.rule_type;
            
            return (
              <div
                key={movement.id}
                className="flex items-center justify-between rounded-lg border border-border bg-background-elevated p-4 transition-colors hover:bg-background"
              >
                <div className="flex-1">
                  <h3 className="font-medium text-foreground">{movement.name}</h3>
                  {movement.primary_pattern && (
                    <p className="mt-1 text-xs text-foreground-muted capitalize">
                      {movement.primary_pattern.replace(/_/g, ' ')}
                    </p>
                  )}
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleToggleRule(movement.id, MovementRuleType.HARD_YES)}
                    className={cn(
                      'flex h-10 w-10 items-center justify-center rounded-lg transition-colors',
                      ruleType === MovementRuleType.HARD_YES
                        ? 'bg-red-500/20 text-red-500'
                        : 'text-foreground-muted hover:bg-background hover:text-red-500'
                    )}
                    aria-label="Mark as favorite"
                    disabled={createRule.isPending || deleteRule.isPending}
                  >
                    <Heart
                      className={cn(
                        'h-5 w-5',
                        ruleType === MovementRuleType.HARD_YES && 'fill-current'
                      )}
                    />
                  </button>
                  
                  <button
                    onClick={() => handleToggleRule(movement.id, MovementRuleType.PREFERRED)}
                    className={cn(
                      'flex h-10 w-10 items-center justify-center rounded-lg transition-colors',
                      ruleType === MovementRuleType.PREFERRED
                        ? 'bg-yellow-500/20 text-yellow-500'
                        : 'text-foreground-muted hover:bg-background hover:text-yellow-500'
                    )}
                    aria-label="Mark as preferred"
                    disabled={createRule.isPending || deleteRule.isPending}
                  >
                    <Star
                      className={cn(
                        'h-5 w-5',
                        ruleType === MovementRuleType.PREFERRED && 'fill-current'
                      )}
                    />
                  </button>
                  
                  <button
                    onClick={() => handleToggleRule(movement.id, MovementRuleType.HARD_NO)}
                    className={cn(
                      'flex h-10 w-10 items-center justify-center rounded-lg transition-colors',
                      ruleType === MovementRuleType.HARD_NO
                        ? 'bg-gray-500/20 text-gray-400'
                        : 'text-foreground-muted hover:bg-background hover:text-gray-400'
                    )}
                    aria-label="Mark to avoid"
                    disabled={createRule.isPending || deleteRule.isPending}
                  >
                    <Ban className="h-5 w-5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

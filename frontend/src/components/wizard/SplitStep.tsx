import { SplitTemplate } from '@/types';
import { useProgramWizardStore } from '@/stores/program-wizard-store';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

const SPLIT_TEMPLATES = [
  { 
    id: SplitTemplate.UPPER_LOWER, 
    name: 'Upper/Lower', 
    description: 'Alternate between upper and lower body days',
    bestFor: '3-4 days/week',
    icon: '↕️'
  },
  { 
    id: SplitTemplate.PPL, 
    name: 'Push/Pull/Legs', 
    description: 'Classic bodybuilding split for volume',
    bestFor: '5-6 days/week',
    icon: '🔄'
  },
  { 
    id: SplitTemplate.FULL_BODY, 
    name: 'Full Body', 
    description: 'Train everything each session',
    bestFor: '2-3 days/week',
    icon: '🏋️'
  },
] as const;

export function SplitStep() {
  const { daysPerWeek, setDaysPerWeek, splitPreference, setSplitPreference } = useProgramWizardStore();

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-xl font-bold">Training Schedule</h2>
        <p className="text-foreground-muted text-sm">
          How often can you train, and what structure works best?
        </p>
      </div>

      {/* Days per week selector */}
      <div className="space-y-3">
        <label className="text-sm font-medium">Days per week</label>
        <div className="grid grid-cols-6 gap-2">
          {[2, 3, 4, 5, 6, 7].map((days) => (
            <button
              key={days}
              onClick={() => setDaysPerWeek(days)}
              className={cn(
                "h-12 rounded-lg font-bold transition-all",
                daysPerWeek === days
                  ? "bg-accent text-background"
                  : "bg-background-elevated hover:bg-border text-foreground"
              )}
            >
              {days}
            </button>
          ))}
        </div>
        <p className="text-xs text-foreground-muted text-center">
          {daysPerWeek <= 3 && "Great for recovery and consistency"}
          {daysPerWeek === 4 && "Sweet spot for most lifters"}
          {daysPerWeek === 5 && "Good volume and frequency balance"}
          {daysPerWeek >= 6 && "High frequency - ensure adequate recovery"}
        </p>
      </div>

      {/* Split template selection */}
      <div className="space-y-3">
        <label className="text-sm font-medium">Training Split</label>
        <div className="grid gap-3">
          {SPLIT_TEMPLATES.map((split) => (
            <Card
              key={split.id}
              variant="interactive"
              selected={splitPreference === split.id}
              onClick={() => setSplitPreference(split.id)}
              className="p-4"
            >
              <div className="flex items-center gap-4">
                <div className="text-2xl">{split.icon}</div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold">{split.name}</h3>
                  <p className="text-xs text-foreground-muted">{split.description}</p>
                </div>
                <div className="text-xs text-accent font-medium">
                  {split.bestFor}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Recommendation based on days */}
      {splitPreference && (
        <div className="bg-accent/10 rounded-lg p-4">
          <p className="text-sm text-foreground-muted">
            {splitPreference === SplitTemplate.FULL_BODY && daysPerWeek > 4 && (
              <span className="text-accent">💡 Consider PPL or Upper/Lower for {daysPerWeek} days/week</span>
            )}
            {splitPreference === SplitTemplate.PPL && daysPerWeek < 5 && (
              <span className="text-accent">💡 PPL works best with 5-6 days. Consider Upper/Lower for {daysPerWeek} days.</span>
            )}
            {splitPreference === SplitTemplate.UPPER_LOWER && (
              <span className="text-cta">✓ Great choice for {daysPerWeek} days/week!</span>
            )}
            {splitPreference === SplitTemplate.HYBRID && (
              <span className="text-cta">✓ Jerome will customize your split based on goals</span>
            )}
            {splitPreference === SplitTemplate.PPL && daysPerWeek >= 5 && (
              <span className="text-cta">✓ Perfect frequency for PPL!</span>
            )}
            {splitPreference === SplitTemplate.FULL_BODY && daysPerWeek <= 4 && (
              <span className="text-cta">✓ Full body is great for {daysPerWeek} days/week!</span>
            )}
          </p>
        </div>
      )}
    </div>
  );
}

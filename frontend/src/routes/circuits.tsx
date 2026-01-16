import { useState } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Flame, Clock, ListChecks } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/common/Spinner';
import { useCircuits } from '@/api/circuits';
import { CircuitType, type CircuitTemplate } from '@/types';

export const Route = createFileRoute('/circuits')({
  component: CircuitsPage,
});

type CircuitFilter = 'all' | CircuitType;

const CIRCUIT_FILTERS: { key: CircuitFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: CircuitType.ROUNDS_FOR_TIME, label: 'Rounds for time' },
  { key: CircuitType.AMRAP, label: 'AMRAP' },
  { key: CircuitType.EMOM, label: 'EMOM' },
  { key: CircuitType.CHIPPER, label: 'Chipper' },
  { key: CircuitType.LADDER, label: 'Ladder' },
  { key: CircuitType.TABATA, label: 'Tabata' },
  { key: CircuitType.STATION, label: 'Station' },
];

function CircuitsPage() {
  const [filter, setFilter] = useState<CircuitFilter>('all');
  const { data: circuits, isLoading } = useCircuits(filter);

  if (isLoading) {
    return (
      <div className="container-app py-6 flex justify-center">
        <Spinner size="sm" />
      </div>
    );
  }

  return (
    <div className="container-app py-6 space-y-4 animate-fade-in">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold">Circuits</h1>
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1">
        {CIRCUIT_FILTERS.map((f) => (
          <Button
            key={f.key}
            size="sm"
            variant={filter === f.key ? 'cta' : 'secondary'}
            onClick={() => setFilter(f.key)}
            className="whitespace-nowrap"
          >
            {f.label}
          </Button>
        ))}
      </div>

      {!circuits || circuits.length === 0 ? (
        <Card className="p-6 text-center">
          <div className="text-foreground-muted">No circuits found for this filter.</div>
        </Card>
      ) : (
        <div className="space-y-3">
          {circuits.map((circuit) => (
            <CircuitCard key={circuit.id} circuit={circuit} />
          ))}
        </div>
      )}
    </div>
  );
}

interface CircuitCardProps {
  circuit: CircuitTemplate;
}

function CircuitCard({ circuit }: CircuitCardProps) {
  const formatType = (type: CircuitType) => type.replace(/_/g, ' ');

  return (
    <Card className="p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h2 className="font-medium">{circuit.name}</h2>
            <span className="inline-flex items-center rounded-full bg-accent/10 px-2 py-0.5 text-[10px] font-medium text-accent uppercase tracking-wide">
              {formatType(circuit.circuit_type)}
            </span>
          </div>
          {circuit.description && (
            <p className="text-xs text-foreground-muted">{circuit.description}</p>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 text-xs text-foreground-muted">
          {circuit.default_rounds && (
            <span className="inline-flex items-center gap-1">
              <ListChecks className="h-3 w-3" />
              {circuit.default_rounds} rounds
            </span>
          )}
          {circuit.default_duration_seconds && (
            <span className="inline-flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {Math.round(circuit.default_duration_seconds / 60)} min
            </span>
          )}
          <span className="inline-flex items-center gap-1">
            <Flame className="h-3 w-3" />
            Level {circuit.difficulty_tier}
          </span>
        </div>
      </div>

      {circuit.tags && circuit.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {circuit.tags.map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-border px-2 py-0.5 text-[10px] text-foreground-muted"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </Card>
  );
}

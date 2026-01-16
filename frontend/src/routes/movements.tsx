import { useMemo, useState } from 'react';
import { createFileRoute } from '@tanstack/react-router';
import { Filter, Search, Settings2, Plus, ArrowUp, ArrowDown, User, X } from 'lucide-react';
import { useMovements, useCreateMovement } from '@/api/settings';
import { MovementPattern, type Movement, type MovementCreate } from '@/types';
import { cn } from '@/lib/utils';

export const Route = createFileRoute('/movements')({
  component: MovementsPage,
});

type ColumnId =
  | 'name'
  | 'primary_pattern'
  | 'primary_region'
  | 'default_equipment'
  | 'equipment_tags'
  | 'complexity'
  | 'skill_level'
  | 'is_compound'
  | 'cns_load'
  | 'metric_type'
  | 'user_id'; // Add user_id column

interface ColumnConfig {
  id: ColumnId;
  label: string;
  render: (movement: Movement) => React.ReactNode;
}

const ALL_COLUMNS: ColumnConfig[] = [
  {
    id: 'name',
    label: 'Name',
    render: (m) => (
      <div className="flex items-center gap-2">
        <span>{m.name}</span>
        {m.user_id && (
          <span title="Custom Movement" className="text-accent">
            <User className="h-3 w-3" />
          </span>
        )}
      </div>
    ),
  },
  {
    id: 'primary_pattern',
    label: 'Pattern',
    render: (m) => m.primary_pattern ?? '',
  },
  {
    id: 'primary_region',
    label: 'Primary Region',
    render: (m) => m.primary_region ?? '',
  },
  {
    id: 'default_equipment',
    label: 'Default Equipment',
    render: (m) => m.default_equipment ?? '',
  },
  {
    id: 'equipment_tags',
    label: 'Equipment Tags',
    render: (m) => (m.equipment_tags && m.equipment_tags.length > 0 ? m.equipment_tags.join(', ') : ''),
  },
  {
    id: 'complexity',
    label: 'Complexity',
    render: (m) => m.complexity ?? '',
  },
  {
    id: 'skill_level',
    label: 'Skill Level',
    render: (m) => m.skill_level ?? '',
  },
  {
    id: 'is_compound',
    label: 'Compound',
    render: (m) => (m.is_compound != null ? (m.is_compound ? 'Yes' : 'No') : ''),
  },
  {
    id: 'cns_load',
    label: 'CNS Load',
    render: (m) => m.cns_load ?? '',
  },
  {
    id: 'metric_type',
    label: 'Metric Type',
    render: (m) => m.metric_type ?? '',
  },
];

const DEFAULT_VISIBLE_COLUMNS: ColumnId[] = [
  'name',
  'primary_pattern',
  'primary_region',
  'default_equipment',
  'complexity',
  'is_compound',
];

type SortConfig = {
  key: ColumnId;
  direction: 'asc' | 'desc';
} | null;

function AddMovementModal({ onClose }: { onClose: () => void }) {
  const createMutation = useCreateMovement();
  const [formData, setFormData] = useState<MovementCreate>({
    name: '',
    pattern: MovementPattern.SQUAT,
    compound: true,
    default_equipment: 'Barbell',
    primary_region: 'Lower Body',
  });
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.name) {
      setError('Name is required');
      return;
    }
    try {
      await createMutation.mutateAsync(formData);
      onClose();
    } catch (err) {
      setError('Failed to create movement. Name might be taken.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-lg bg-background-elevated border border-border p-6 shadow-xl">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-foreground">Add Custom Movement</h2>
          <button onClick={onClose} className="text-foreground-muted hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        {error && (
          <div className="mb-4 rounded bg-destructive/10 p-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-accent focus:outline-none"
              placeholder="e.g. My Custom Squat"
            />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">Pattern</label>
            <select
              value={formData.pattern}
              onChange={(e) => setFormData({ ...formData, pattern: e.target.value as MovementPattern })}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-accent focus:outline-none"
            >
              {Object.values(MovementPattern).map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-foreground">Equipment</label>
            <input
              type="text"
              value={formData.default_equipment}
              onChange={(e) => setFormData({ ...formData, default_equipment: e.target.value })}
              className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-accent focus:outline-none"
            />
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="compound"
              checked={formData.compound}
              onChange={(e) => setFormData({ ...formData, compound: e.target.checked })}
              className="h-4 w-4 rounded border-border bg-background text-accent"
            />
            <label htmlFor="compound" className="text-sm font-medium text-foreground">
              Compound Movement
            </label>
          </div>

          <div className="mt-6 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg px-4 py-2 text-sm font-medium text-foreground-muted hover:bg-background"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="rounded-lg bg-cta px-4 py-2 text-sm font-medium text-background hover:bg-cta/90 disabled:opacity-50"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Movement'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function MovementsPage() {
  const { data, isLoading, error } = useMovements({ limit: 200 });
  const [search, setSearch] = useState('');
  const [selectedPattern, setSelectedPattern] = useState<MovementPattern | 'all'>('all');
  const [selectedEquipment, setSelectedEquipment] = useState<string | 'all'>('all');
  const [visibleColumns, setVisibleColumns] = useState<ColumnId[]>(DEFAULT_VISIBLE_COLUMNS);
  const [showColumnPicker, setShowColumnPicker] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [sortConfig, setSortConfig] = useState<SortConfig>(null);

  const movements: Movement[] = useMemo(
    () => data?.movements ?? [],
    [data],
  );

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
    { value: MovementPattern.CONDITIONING, label: 'Conditioning' },
    { value: MovementPattern.CARDIO, label: 'Cardio' },
  ];

  const equipmentOptions = useMemo(() => {
    const set = new Set<string>();
    for (const m of movements) {
      if (m.default_equipment) {
        set.add(m.default_equipment);
      }
      if (m.equipment_tags) {
        for (const tag of m.equipment_tags) {
          set.add(tag);
        }
      }
    }
    return ['all', ...Array.from(set).sort()];
  }, [movements]);

  const filteredMovements = useMemo(() => {
    let result = movements.filter((movement) => {
      const matchesSearch = movement.name.toLowerCase().includes(search.toLowerCase());
      const matchesPattern =
        selectedPattern === 'all' ||
        movement.primary_pattern === selectedPattern;

      const matchesEquipment =
        selectedEquipment === 'all' ||
        movement.default_equipment === selectedEquipment ||
        (movement.equipment_tags && movement.equipment_tags.includes(selectedEquipment));

      return matchesSearch && matchesPattern && matchesEquipment;
    });

    if (sortConfig) {
      result = [...result].sort((a, b) => {
        let aValue: any = a[sortConfig.key as keyof Movement];
        let bValue: any = b[sortConfig.key as keyof Movement];

        // Handle specific columns if needed
        if (sortConfig.key === 'is_compound') {
          aValue = a.is_compound ? 1 : 0;
          bValue = b.is_compound ? 1 : 0;
        }

        if (aValue == null) aValue = '';
        if (bValue == null) bValue = '';

        if (aValue < bValue) return sortConfig.direction === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return result;
  }, [movements, search, selectedPattern, selectedEquipment, sortConfig]);

  const toggleColumn = (id: ColumnId) => {
    setVisibleColumns((current) =>
      current.includes(id) ? current.filter((col) => col !== id) : [...current, id],
    );
  };

  const handleSort = (key: ColumnId) => {
    setSortConfig((current) => {
      if (current?.key === key) {
        if (current.direction === 'asc') return { key, direction: 'desc' };
        return null;
      }
      return { key, direction: 'asc' };
    });
  };

  const columnsToRender = ALL_COLUMNS.filter((col) => visibleColumns.includes(col.id));

  return (
    <div className="container-app py-6">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Movement Library</h1>
          <p className="mt-2 text-sm text-foreground-muted">
            Browse all movements with filters and customizable columns.
          </p>
        </div>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-cta px-4 py-2 text-sm font-medium text-background hover:bg-cta/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Custom Movement
        </button>
      </div>

      <div className="mb-4 grid grid-cols-1 gap-3 md:grid-cols-3">
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-muted" />
          <input
            type="text"
            placeholder="Search movements..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-border bg-background-elevated px-9 py-2 text-sm text-foreground placeholder:text-foreground-muted focus:border-accent focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-foreground-muted" />
          <select
            value={selectedPattern}
            onChange={(e) =>
              setSelectedPattern(
                e.target.value === 'all'
                  ? 'all'
                  : (e.target.value as MovementPattern),
              )
            }
            className="h-9 flex-1 rounded-lg border border-border bg-background-elevated px-2 text-xs text-foreground"
          >
            {patternOptions.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-foreground-muted" />
          <select
            value={selectedEquipment}
            onChange={(e) =>
              setSelectedEquipment(e.target.value as typeof selectedEquipment)
            }
            className="h-9 flex-1 rounded-lg border border-border bg-background-elevated px-2 text-xs text-foreground"
          >
            {equipmentOptions.map((opt) => (
              <option key={opt} value={opt}>
                {opt === 'all' ? 'All Equipment' : opt}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="text-xs text-foreground-muted">
          Showing {filteredMovements.length} of {movements.length} movements
        </div>
        <button
          type="button"
          onClick={() => setShowColumnPicker((prev) => !prev)}
          className={cn(
            'inline-flex items-center gap-2 rounded-lg border border-border bg-background-elevated px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-background',
          )}
        >
          <Settings2 className="h-4 w-4" />
          Columns
        </button>
      </div>

      {showColumnPicker && (
        <div className="mb-4 rounded-lg border border-border bg-background-elevated p-3">
          <p className="mb-2 text-xs font-medium text-foreground-muted">
            Select columns to display:
          </p>
          <div className="flex flex-wrap gap-3">
            {ALL_COLUMNS.map((col) => (
              <label key={col.id} className="flex items-center gap-2 text-xs text-foreground">
                <input
                  type="checkbox"
                  checked={visibleColumns.includes(col.id)}
                  onChange={() => toggleColumn(col.id)}
                  className="h-3 w-3 rounded border-border bg-background-elevated text-accent"
                />
                <span>{col.label}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      <div className="rounded-lg border border-border bg-background-elevated">
        {isLoading ? (
          <div className="py-10 text-center text-foreground-muted text-sm">
            Loading movements...
          </div>
        ) : error ? (
          <div className="py-10 text-center text-foreground-muted text-sm">
            Failed to load movements. Please check your connection.
          </div>
        ) : filteredMovements.length === 0 ? (
          <div className="py-10 text-center text-foreground-muted text-sm">
            No movements match your filters.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <div className="max-h-[480px] overflow-y-auto">
              <table className="min-w-full text-left text-xs">
                <thead className="sticky top-0 bg-background-elevated border-b border-border z-10">
                  <tr>
                    {columnsToRender.map((col) => (
                      <th
                        key={col.id}
                        className="px-3 py-2 font-semibold text-foreground-muted whitespace-nowrap cursor-pointer hover:text-foreground hover:bg-background/50 select-none"
                        onClick={() => handleSort(col.id)}
                      >
                        <div className="flex items-center gap-1">
                          {col.label}
                          {sortConfig?.key === col.id && (
                            sortConfig.direction === 'asc' ? (
                              <ArrowUp className="h-3 w-3 text-accent" />
                            ) : (
                              <ArrowDown className="h-3 w-3 text-accent" />
                            )
                          )}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filteredMovements.map((movement) => (
                    <tr
                      key={movement.id}
                      className="border-b border-border/60 last:border-b-0 hover:bg-background"
                    >
                      {columnsToRender.map((col) => (
                        <td key={col.id} className="px-3 py-1.5 text-foreground whitespace-nowrap">
                          {col.render(movement)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {isModalOpen && <AddMovementModal onClose={() => setIsModalOpen(false)} />}
    </div>
  );
}

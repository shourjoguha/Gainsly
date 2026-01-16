import { useState } from 'react';
import { createFileRoute, Link } from '@tanstack/react-router';
import { ChevronDown, ChevronRight, Trash2 } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Spinner } from '@/components/common/Spinner';
import { usePrograms, useDeleteProgram, useUpdateProgram } from '@/api/programs';
import type { Program } from '@/types';

export const Route = createFileRoute('/programs')({
  component: ProgramsHistoryPage,
});

function ProgramsHistoryPage() {
  const { data: programs, isLoading } = usePrograms(false);
  const deleteMutation = useDeleteProgram();
  const updateMutation = useUpdateProgram();
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());

  const toggleExpanded = (id: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleDelete = async (program: Program) => {
    if (deleteMutation.isPending) return;
    await deleteMutation.mutateAsync(program.id);
  };

  const handleNameBlur = async (program: Program, value: string) => {
    const trimmed = value.trim();
    if (trimmed === (program.name || '').trim()) return;
    await updateMutation.mutateAsync({ id: program.id, data: { name: trimmed || null } });
  };

  const formatDate = (dateStr: string | null | undefined) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'numeric', day: 'numeric', year: '2-digit' });
  };

  const formatSplit = (split: string) => split.replace('_', ' ');

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
        <h1 className="text-xl font-semibold">Programs</h1>
        <Button variant="secondary" asChild>
          <Link to="/program/new">New Program</Link>
        </Button>
      </div>

      {!programs || programs.length === 0 ? (
        <Card className="p-6 text-center">
          <div className="text-foreground-muted mb-2">No programs yet</div>
          <Button variant="outline" asChild>
            <Link to="/program/new">Create your first program</Link>
          </Button>
        </Card>
      ) : (
        <div className="space-y-3">
          {programs.map((program) => {
            const expanded = expandedIds.has(program.id);
            const weeks = program.duration_weeks;
            const daysPerWeek = program.days_per_week || 7;

            return (
              <Card key={program.id} className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <button
                    type="button"
                    className="flex flex-1 items-center gap-3 text-left"
                    onClick={() => toggleExpanded(program.id)}
                  >
                    {expanded ? (
                      <ChevronDown className="h-4 w-4 text-foreground-muted" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-foreground-muted" />
                    )}
                    <div className="flex-1 space-y-1">
                      <input
                        type="text"
                        defaultValue={program.name || ''}
                        placeholder="Program name"
                        onBlur={(e) => handleNameBlur(program, e.target.value)}
                        className="w-full bg-transparent border-b border-border/60 focus:border-accent text-sm font-medium outline-none"
                      />
                      <div className="text-xs text-foreground-muted flex items-center gap-2">
                        <span className="capitalize">{formatSplit(program.split_template)}</span>
                        <span>·</span>
                        <span>{program.duration_weeks} weeks</span>
                        <span>·</span>
                        <span>{program.days_per_week} days/week</span>
                        {program.created_at && (
                          <>
                            <span>·</span>
                            <span>Created {formatDate(program.created_at)}</span>
                          </>
                        )}
                      </div>
                    </div>
                  </button>

                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      asChild
                    >
                      <Link to="/program/$programId" params={{ programId: String(program.id) }}>
                        View
                      </Link>
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(program)}
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </div>

                {expanded && (
                  <div className="mt-4 border-t border-border/60 pt-4 space-y-3">
                    <div className="text-xs text-foreground-muted">Weeks × Days overview</div>
                    <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
                      {Array.from({ length: weeks }).map((_, weekIndex) => (
                        <div key={weekIndex} className="flex items-center gap-3">
                          <div className="w-14 text-xs text-foreground-muted">Week {weekIndex + 1}</div>
                          <div className="flex-1 overflow-x-auto">
                            <div className="flex gap-2 min-w-max">
                              {Array.from({ length: daysPerWeek }).map((__, dayIndex) => (
                                <div
                                  key={dayIndex}
                                  className="w-10 h-10 rounded-md border border-border bg-background-elevated flex items-center justify-center text-xs text-foreground-muted"
                                >
                                  D{dayIndex + 1}
                                </div>
                              ))}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

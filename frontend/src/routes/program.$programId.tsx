import { createFileRoute, Link } from '@tanstack/react-router';
import { useProgram } from '@/api/programs';
import { ArrowLeft, Play, MessageSquare, Calendar, Target, Dumbbell } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Spinner } from '@/components/common/Spinner';
import { SessionCard } from '@/components/program/SessionCard';
import { Goal, SessionType } from '@/types';

export const Route = createFileRoute('/program/$programId')({
  component: ProgramDetailPage,
});

// Goal display labels and colors
const GOAL_CONFIG: Record<Goal, { label: string; color: string }> = {
  [Goal.STRENGTH]: { label: 'Strength', color: 'bg-red-500' },
  [Goal.HYPERTROPHY]: { label: 'Hypertrophy', color: 'bg-purple-500' },
  [Goal.ENDURANCE]: { label: 'Endurance', color: 'bg-blue-500' },
  [Goal.FAT_LOSS]: { label: 'Fat Loss', color: 'bg-orange-500' },
  [Goal.MOBILITY]: { label: 'Mobility', color: 'bg-green-500' },
  [Goal.EXPLOSIVENESS]: { label: 'Explosiveness', color: 'bg-yellow-500' },
  [Goal.SPEED]: { label: 'Speed', color: 'bg-cyan-500' },
};

function ProgramDetailPage() {
  const { programId } = Route.useParams();
  const { data, isLoading, error } = useProgram(Number(programId));

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="container-app py-6">
        <div className="text-center py-12">
          <h2 className="text-xl font-semibold text-foreground-muted">
            Program not found
          </h2>
          <Link to="/" className="text-accent hover:underline mt-2 inline-block">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const { program, active_microcycle, upcoming_sessions } = data;

  // Build goals array for display
  const goals = [
    { goal: program.goal_1, weight: program.goal_weight_1 },
    { goal: program.goal_2, weight: program.goal_weight_2 },
    { goal: program.goal_3, weight: program.goal_weight_3 },
  ].sort((a, b) => b.weight - a.weight);

  // Group sessions by training vs rest
  const trainingSessions = upcoming_sessions.filter(
    (s) => s.session_type !== SessionType.RECOVERY
  );

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-background/95 backdrop-blur border-b border-border">
        <div className="container-app py-3">
          <div className="flex items-center gap-3">
            <Link to="/" className="text-foreground-muted hover:text-foreground">
              <ArrowLeft className="h-5 w-5" />
            </Link>
            <div className="flex-1">
              <h1 className="text-lg font-semibold">Your Program</h1>
              <p className="text-xs text-foreground-muted">
                {program.duration_weeks} weeks • {program.split_template.replace('_', ' ')}
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 container-app py-6 space-y-6">
        {/* Goals Section */}
        <section>
          <h2 className="text-sm font-medium text-foreground-muted mb-3 flex items-center gap-2">
            <Target className="h-4 w-4" />
            Goals
          </h2>
          <div className="flex gap-2 flex-wrap">
            {goals.map(({ goal, weight }) => {
              const config = GOAL_CONFIG[goal];
              return (
                <div
                  key={goal}
                  className="flex items-center gap-2 px-3 py-1.5 bg-background-elevated rounded-full"
                >
                  <div className={`w-2 h-2 rounded-full ${config.color}`} />
                  <span className="text-sm">{config.label}</span>
                  <span className="text-xs text-foreground-muted">{weight}/10</span>
                </div>
              );
            })}
          </div>
        </section>

        {/* Microcycle Info */}
        {active_microcycle && (
          <section>
            <h2 className="text-sm font-medium text-foreground-muted mb-3 flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Week {active_microcycle.sequence_number}
              {active_microcycle.is_deload && (
                <span className="text-xs bg-accent/20 text-accent px-2 py-0.5 rounded">
                  Deload
                </span>
              )}
            </h2>
          </section>
        )}

        {/* Quick Actions */}
        <div className="flex gap-3">
          <Button variant="cta" className="flex-1" asChild>
            <Link to="/">
              <Play className="h-4 w-4 mr-2" />
              Start Workout
            </Link>
          </Button>
          <Button variant="secondary" className="flex-1" asChild>
            <Link to="/">
              <MessageSquare className="h-4 w-4 mr-2" />
              Adapt Session
            </Link>
          </Button>
        </div>

        {/* Sessions List */}
        <section>
          <h2 className="text-sm font-medium text-foreground-muted mb-3 flex items-center gap-2">
            <Dumbbell className="h-4 w-4" />
            Upcoming Sessions ({trainingSessions.length})
          </h2>
          
          {upcoming_sessions.length === 0 ? (
            <Card className="p-6 text-center">
              <p className="text-foreground-muted">No sessions scheduled</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {upcoming_sessions.map((session) => (
                <SessionCard key={session.id} session={session} />
              ))}
            </div>
          )}
        </section>

        {/* Program Stats */}
        <section>
          <h2 className="text-sm font-medium text-foreground-muted mb-3">
            Program Details
          </h2>
          <Card className="p-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-foreground-muted">Split</span>
                <p className="font-medium capitalize">
                  {program.split_template.replace('_', ' ')}
                </p>
              </div>
              <div>
                <span className="text-foreground-muted">Progression</span>
                <p className="font-medium capitalize">
                  {program.progression_style.replace('_', ' ')}
                </p>
              </div>
              <div>
                <span className="text-foreground-muted">Duration</span>
                <p className="font-medium">{program.duration_weeks} weeks</p>
              </div>
              <div>
                <span className="text-foreground-muted">Deload</span>
                <p className="font-medium">
                  Every {program.deload_every_n_microcycles} weeks
                </p>
              </div>
            </div>
          </Card>
        </section>
      </main>
    </div>
  );
}

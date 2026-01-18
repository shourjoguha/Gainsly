import { useEffect, useState } from 'react';
import { createFileRoute, Link } from '@tanstack/react-router';
import { useProgram } from '@/api/programs';
import { ArrowLeft, Play, MessageSquare, Calendar, Target, Dumbbell, LineChart, ChevronLeft, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Spinner } from '@/components/common/Spinner';
import { SessionCard } from '@/components/program/SessionCard';
import { Goal, SessionType, Session } from '@/types';

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

const PROGRESSION_DESCRIPTIONS: Record<string, string> = {
  single_progression:
    'Focus on increasing weight once you hit the top of your rep range.',
  double_progression:
    'Increase reps first. Once you hit the top of the range for all sets, increase the weight.',
  wave_loading:
    'Vary intensity in waves (e.g., 7-5-3 reps) to manage fatigue and break plateaus.',
  paused_variations: 'Use pauses to increase difficulty without adding weight.',
  build_to_drop:
    'Build to a top heavy set, then drop weight for volume work.',
};

function sessionHasContent(session: Session): boolean {
  const hasMain =
    !!session.main && session.main.length > 0;

  const hasWarmup =
    !!session.warmup && session.warmup.length > 0;

  const hasAccessory =
    !!session.accessory && session.accessory.length > 0;

  const hasCooldown =
    !!session.cooldown && session.cooldown.length > 0;

  const hasFinisherExercises =
    !!session.finisher?.exercises &&
    session.finisher.exercises.length > 0;

  const hasFinisherDuration =
    !!session.finisher?.duration_minutes;

  return (
    hasMain ||
    hasWarmup ||
    hasAccessory ||
    hasCooldown ||
    hasFinisherExercises ||
    hasFinisherDuration
  );
}

function useProgramWithGeneration(programId: number) {
  const query = useProgram(programId);

  const { data, isLoading, error, refetch } = query;

  const trainingSessions =
    data?.upcoming_sessions.filter(
      (s) => s.session_type !== SessionType.RECOVERY
    ) ?? [];

  const totalTraining = trainingSessions.length;
  const generatedCount = trainingSessions.filter(sessionHasContent).length;

  const isGenerating =
    totalTraining > 0 && generatedCount < totalTraining;

  const shouldPoll =
    !!data &&
    !isLoading &&
    !error &&
    totalTraining > 0 &&
    generatedCount < totalTraining;

  useEffect(() => {
    if (!shouldPoll) {
      return;
    }

    const id = window.setInterval(() => {
      refetch();
    }, 4000);

    return () => window.clearInterval(id);
  }, [shouldPoll, refetch]);

  return {
    ...query,
    isGenerating,
  };
}

function ProgramDetailPage() {
  const { programId } = Route.useParams();
  const { data, isLoading, error, isGenerating } = useProgramWithGeneration(
    Number(programId)
  );
  const [weekOffset, setWeekOffset] = useState(0);

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

  const { program, active_microcycle, upcoming_sessions, microcycles } = data;
 
  // Build goals array for display
  const goals = [
    { goal: program.goal_1, weight: program.goal_weight_1 },
    { goal: program.goal_2, weight: program.goal_weight_2 },
    { goal: program.goal_3, weight: program.goal_weight_3 },
  ].sort((a, b) => b.weight - a.weight);

  const totalWeeks = program.duration_weeks;
  const baseWeek = active_microcycle?.sequence_number ?? 1;
  const weekInView = Math.min(
    totalWeeks,
    Math.max(1, baseWeek + weekOffset),
  );

  const baseWeekMicroSessions =
    microcycles?.find((mc) => mc.sequence_number === baseWeek)?.sessions ?? [];

  const baseTemplateSessions =
    baseWeekMicroSessions.some(sessionHasContent) && baseWeekMicroSessions.length > 0
      ? baseWeekMicroSessions
      : upcoming_sessions;

  const currentWeekMicroSessions =
    microcycles?.find((mc) => mc.sequence_number === weekInView)?.sessions ?? [];

  const sessionsForWeek: Session[] = [];

  const maxLength = Math.max(
    baseTemplateSessions.length,
    currentWeekMicroSessions.length,
  );

  for (let i = 0; i < maxLength; i += 1) {
    const templateSession = baseTemplateSessions[i];
    const weekSession =
      weekInView === baseWeek
        ? currentWeekMicroSessions[i] ?? templateSession
        : currentWeekMicroSessions[i];

    if (!weekSession && templateSession) {
      sessionsForWeek.push(templateSession);
      continue;
    }

    if (!weekSession) {
      continue;
    }

    if (weekInView === baseWeek) {
      if (sessionHasContent(weekSession) || !templateSession) {
        sessionsForWeek.push(weekSession);
      } else {
        sessionsForWeek.push(templateSession);
      }
      continue;
    }

    if (sessionHasContent(weekSession) || !templateSession) {
      sessionsForWeek.push(weekSession);
    } else {
      sessionsForWeek.push({
        ...templateSession,
        id: weekSession.id,
        microcycle_id: weekSession.microcycle_id,
        day_number: weekSession.day_number,
        session_date: weekSession.session_date,
      });
    }
  }

  // Group sessions by training vs rest
  const trainingSessions = sessionsForWeek.filter(
    (s) => s.session_type !== SessionType.RECOVERY
  );

  const handlePrevWeek = () => {
    setWeekOffset((prev) => {
      const current = baseWeek + prev;
      if (current <= 1) return prev;
      return prev - 1;
    });
  };

  const handleNextWeek = () => {
    setWeekOffset((prev) => {
      const current = baseWeek + prev;
      if (current >= totalWeeks) return prev;
      return prev + 1;
    });
  };

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
        {/* Week Navigation */}
        <section className="flex justify-center">
          <div className="inline-flex items-center gap-4 rounded-full border border-border bg-background-elevated px-4 py-1.5 text-xs">
            <button
              type="button"
              onClick={handlePrevWeek}
              disabled={weekInView <= 1}
              className="text-foreground-muted disabled:opacity-40 disabled:cursor-default"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <div className="flex items-baseline gap-1">
              <span className="text-foreground-muted">Week</span>
              <span className="text-sm font-medium">{weekInView}</span>
              <span className="text-xs text-foreground-muted">/ {totalWeeks}</span>
            </div>
            <button
              type="button"
              onClick={handleNextWeek}
              disabled={weekInView >= totalWeeks}
              className="text-foreground-muted disabled:opacity-40 disabled:cursor-default"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </section>

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

        {/* Progression Strategy Recommendation */}
        <section>
          <h2 className="text-sm font-medium text-foreground-muted mb-3 flex items-center gap-2">
            <LineChart className="h-4 w-4" />
            Progression Strategy
          </h2>
          <Card className="p-4 bg-background-elevated border-none">
             <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-foreground capitalize">
                  {program.progression_style.replace(/_/g, ' ')}
                </span>
                <span className="text-xs bg-accent/20 text-accent px-2 py-1 rounded">Recommended</span>
             </div>
             <p className="text-sm text-foreground-muted">
               {PROGRESSION_DESCRIPTIONS[program.progression_style] || "Follow the prescribed sets and reps."}
             </p>
          </Card>
        </section>

        {/* Microcycle Info */}
        {active_microcycle && (
          <section>
            <h2 className="text-sm font-medium text-foreground-muted mb-3 flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Current Microcycle
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
            Week {weekInView} Sessions ({trainingSessions.length})
          </h2>

          {isGenerating && weekInView === baseWeek && (
            <div className="mb-3 flex items-center gap-2 text-xs text-foreground-muted">
              <Spinner size="sm" />
              <span>Jerome is building your sessions. This can take up to a minute.</span>
            </div>
          )}
          
          {sessionsForWeek.length === 0 ? (
            <Card className="p-6 text-center">
              <p className="text-foreground-muted">No sessions scheduled</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {sessionsForWeek.map((session) => (
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

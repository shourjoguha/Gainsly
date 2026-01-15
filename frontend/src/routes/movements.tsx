import { createFileRoute } from '@tanstack/react-router';
import { Dumbbell } from 'lucide-react';

export const Route = createFileRoute('/movements')({
  component: MovementsPage,
});

function MovementsPage() {
  return (
    <div className="container-app py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">Movement Library</h1>
        <p className="mt-2 text-sm text-foreground-muted">
          Browse and explore all available exercises
        </p>
      </div>

      <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-background-elevated p-12">
        <Dumbbell className="h-16 w-16 text-foreground-muted mb-4" />
        <h2 className="text-lg font-semibold text-foreground mb-2">Coming Soon</h2>
        <p className="text-center text-sm text-foreground-muted max-w-md">
          The Movement Library is under development. Soon you'll be able to browse
          all exercises, view instructions, and explore variations.
        </p>
      </div>
    </div>
  );
}

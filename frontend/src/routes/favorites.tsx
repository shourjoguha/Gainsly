import { createFileRoute } from '@tanstack/react-router';
import { MovementsStep } from '@/components/wizard/MovementsStep';

export const Route = createFileRoute('/favorites')({
  component: FavoritesPage,
});

function FavoritesPage() {
  return (
    <div className="container-app py-6">
      <MovementsStep />
    </div>
  );
}

import { MovementsStep } from '@/components/wizard/MovementsStep';

export function FavoritesTab() {
  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Favorites / Movements</h2>
      <MovementsStep />
    </div>
  );
}

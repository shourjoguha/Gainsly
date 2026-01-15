import { createFileRoute } from '@tanstack/react-router';
import { Settings as SettingsIcon } from 'lucide-react';

export const Route = createFileRoute('/settings')({
  component: SettingsPage,
});

function SettingsPage() {
  return (
    <div className="container-app py-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        <p className="mt-2 text-sm text-foreground-muted">
          Manage your account and preferences
        </p>
      </div>

      <div className="flex flex-col items-center justify-center rounded-lg border border-border bg-background-elevated p-12">
        <SettingsIcon className="h-16 w-16 text-foreground-muted mb-4" />
        <h2 className="text-lg font-semibold text-foreground mb-2">Coming Soon</h2>
        <p className="text-center text-sm text-foreground-muted max-w-md">
          Settings page is under development. Soon you'll be able to customize your
          experience, manage notifications, and adjust preferences.
        </p>
      </div>
    </div>
  );
}

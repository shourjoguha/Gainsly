import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useUserProfile, useUpdateUserProfile } from '@/api/settings';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Spinner } from '@/components/common/Spinner';
import { useUIStore } from '@/stores/ui-store';
import { ExperienceLevel, PersonaTone, PersonaAggression, Sex } from '@/types';
import type { UserProfileUpdate } from '@/types';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { cn } from '@/lib/utils';

export function ProfileTab() {
  const { data: profile, isLoading } = useUserProfile();
  const updateMutation = useUpdateUserProfile();
  const { addToast } = useUIStore();
  const [isAdvancedOpen, setIsAdvancedOpen] = useState(false);

  const { register, handleSubmit, reset, watch, formState: { isDirty } } = useForm<UserProfileUpdate>();

  // Watch values for display
  const disciplinePrefs = watch('discipline_preferences');

  useEffect(() => {
    if (profile) {
      reset({
        name: profile.name,
        experience_level: profile.experience_level,
        persona_tone: profile.persona_tone,
        persona_aggression: profile.persona_aggression,
        date_of_birth: profile.date_of_birth,
        sex: profile.sex,
        height_cm: profile.height_cm,
        discipline_preferences: profile.discipline_preferences || {
          mobility: 5,
          calisthenics: 5,
          olympic_lifts: 0,
          crossfit: 0,
          strength: 10,
        },
        discipline_experience: profile.discipline_experience || {},
        scheduling_preferences: profile.scheduling_preferences || {
          mix_disciplines: true,
          cardio_preference: 'finisher',
        },
        long_term_goal_category: profile.long_term_goal_category || 'general_fitness',
        long_term_goal_description: profile.long_term_goal_description || '',
      });
    }
  }, [profile, reset]);

  const onSubmit = async (data: UserProfileUpdate) => {
    try {
      // Ensure number types
      const payload = {
        ...data,
        height_cm: data.height_cm ? Number(data.height_cm) : undefined,
        persona_aggression: data.persona_aggression ? Number(data.persona_aggression) : undefined,
        discipline_preferences: data.discipline_preferences ? {
          mobility: Number(data.discipline_preferences.mobility),
          calisthenics: Number(data.discipline_preferences.calisthenics),
          olympic_lifts: Number(data.discipline_preferences.olympic_lifts),
          crossfit: Number(data.discipline_preferences.crossfit),
          strength: Number(data.discipline_preferences.strength),
        } : undefined,
      };
      
      await updateMutation.mutateAsync(payload);
      addToast({
        type: 'success',
        message: 'Profile updated successfully',
      });
    } catch (error) {
      addToast({
        type: 'error',
        message: 'Failed to update profile',
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-6">
        <Spinner size="sm" />
      </div>
    );
  }

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-2xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Personal Info */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Name</label>
            <input
              {...register('name')}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="Your name"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Date of Birth</label>
            <input
              type="date"
              {...register('date_of_birth')}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Sex</label>
            <select
              {...register('sex')}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">Select sex</option>
              {Object.values(Sex).map((value) => (
                <option key={value} value={value} className="capitalize">
                  {value}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Height (cm)</label>
            <input
              type="number"
              {...register('height_cm')}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              placeholder="175"
            />
          </div>

          {/* Training Profile */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Experience Level</label>
            <select
              {...register('experience_level')}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {Object.values(ExperienceLevel).map((value) => (
                <option key={value} value={value} className="capitalize">
                  {value.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Persona Tone</label>
            <select
              {...register('persona_tone')}
              className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              {Object.values(PersonaTone).map((value) => (
                <option key={value} value={value} className="capitalize">
                  {value.replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-2 md:col-span-2">
            <label className="text-sm font-medium">Coach Aggression (1-5)</label>
            <div className="flex items-center gap-4">
              <input
                type="range"
                min="1"
                max="5"
                step="1"
                {...register('persona_aggression')}
                className="flex-1"
              />
              <span className="text-sm font-medium w-8 text-center">
                {/* We rely on form state but range input is tricky to display value without watching */}
              </span>
            </div>
             <div className="flex justify-between text-xs text-foreground-muted">
                <span>Conservative</span>
                <span>Aggressive</span>
              </div>
          </div>

          {/* Long Term Goals */}
          <div className="space-y-4 md:col-span-2 pt-4 border-t border-border">
            <h4 className="text-sm font-semibold text-foreground">Long Term Goals</h4>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Primary Goal Category</label>
                <select
                  {...register('long_term_goal_category')}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="general_fitness">General Fitness</option>
                  <option value="muscle_gain">Muscle Gain</option>
                  <option value="fat_loss">Fat Loss</option>
                  <option value="strength">Strength</option>
                  <option value="performance">Performance</option>
                  <option value="health_longevity">Health & Longevity</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Goal Description</label>
                <textarea
                  {...register('long_term_goal_description')}
                  className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring min-h-[100px]"
                  placeholder="Describe your goal for the next 1-3 years (e.g., run a marathon, gain 10lbs of muscle)"
                />
                <p className="text-xs text-foreground-muted">
                  What do you want to achieve over the next 1-3 years?
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Advanced Filters Section */}
        <div className="border rounded-lg border-border">
          <button
            type="button"
            onClick={() => setIsAdvancedOpen(!isAdvancedOpen)}
            className="flex w-full items-center justify-between p-4 text-sm font-medium hover:bg-background-elevated transition-colors rounded-lg"
          >
            <span>Advanced Filters</span>
            {isAdvancedOpen ? (
              <ChevronUp className="h-4 w-4 text-foreground-muted" />
            ) : (
              <ChevronDown className="h-4 w-4 text-foreground-muted" />
            )}
          </button>
          
          {isAdvancedOpen && (
            <div className="p-4 pt-0 space-y-6 border-t border-border mt-2 animate-in slide-in-from-top-2">
              <div className="space-y-4">
                <h4 className="text-sm font-semibold text-foreground">Discipline Interests (0-10)</h4>
                <p className="text-xs text-foreground-muted">
                  Set the relative priority for different training styles. 0 means you don't want it, 10 means it's a high priority.
                </p>
                
                <div className="space-y-4">
                  {(
                    [
                      { key: 'strength', label: 'Strength & Hypertrophy' },
                      { key: 'mobility', label: 'Mobility & Flexibility' },
                      { key: 'calisthenics', label: 'Calisthenics (Bodyweight)' },
                      { key: 'olympic_lifts', label: 'Olympic Weightlifting' },
                      { key: 'crossfit', label: 'CrossFit / Metcon' },
                    ] as const
                  ).map((discipline) => (
                    <div key={discipline.key} className="space-y-1">
                      <div className="flex justify-between">
                        <label className="text-xs font-medium">{discipline.label}</label>
                        <span className="text-xs text-foreground-muted">
                          {disciplinePrefs?.[discipline.key] || 0}
                        </span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="10"
                        step="1"
                        {...register(`discipline_preferences.${discipline.key}`)}
                        className="w-full"
                      />
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-4 pt-4 border-t border-border">
                <h4 className="text-sm font-semibold text-foreground">Experience Level (per Discipline)</h4>
                <p className="text-xs text-foreground-muted">
                  Specify your experience level for each discipline to tailor the program intensity.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {(
                    [
                      { key: 'strength', label: 'Strength' },
                      { key: 'mobility', label: 'Mobility' },
                      { key: 'calisthenics', label: 'Calisthenics' },
                      { key: 'olympic_lifts', label: 'Olympic Lifts' },
                      { key: 'crossfit', label: 'CrossFit' },
                    ] as const
                  ).map((discipline) => (
                    <div key={discipline.key} className="space-y-1">
                      <label className="text-xs font-medium">{discipline.label}</label>
                      <select
                        {...register(`discipline_experience.${discipline.key}`)}
                        className="w-full rounded-md border border-border bg-background px-2 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-ring"
                      >
                        <option value="">Select Level</option>
                        {Object.values(ExperienceLevel).map((level) => (
                          <option key={level} value={level}>
                            {level.replace('_', ' ')}
                          </option>
                        ))}
                      </select>
                    </div>
                  ))}
                </div>
              </div>

              <div className="space-y-4 pt-4 border-t border-border">
                <h4 className="text-sm font-semibold text-foreground">Scheduling Preferences</h4>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <label className="text-sm font-medium">Mix Disciplines</label>
                    <p className="text-xs text-foreground-muted">
                      Allow combining different styles (e.g. mobility + strength) in a single session.
                    </p>
                  </div>
                  <input
                    type="checkbox"
                    {...register('scheduling_preferences.mix_disciplines')}
                    className="h-4 w-4 rounded border-border text-accent focus:ring-accent"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Conditioning & Cardio</label>
                  <p className="text-xs text-foreground-muted">How should we schedule your cardio?</p>
                  <select
                    {...register('scheduling_preferences.cardio_preference')}
                    className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    <option value="none">None / I do it separately</option>
                    <option value="finisher">Add as finishers (10-20 mins)</option>
                    <option value="dedicated_day">Dedicated conditioning day</option>
                    <option value="mixed">Mix both (finishers + dedicated)</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end pt-4">
          <Button type="submit" disabled={!isDirty || updateMutation.isPending}>
            {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </form>
    </Card>
  );
}

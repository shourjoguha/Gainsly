import { useState, useEffect } from 'react';
import { createFileRoute, useNavigate } from '@tanstack/react-router';
import type { AxiosError } from 'axios';
import { useProgramWizardStore } from '@/stores/program-wizard-store';
import { useCreateProgram } from '@/api/programs';
import { WizardContainer } from '@/components/wizard/WizardContainer';
import {
  GoalsStep,
  SplitStep,
  DisciplinesStep,
  MovementsStep,
  ActivitiesStep,
  CoachStep,
} from '@/components/wizard';
import { 
  SplitTemplate, 
  PersonaTone, 
  PersonaAggression,
  type ProgramCreate 
} from '@/types';
import { useUIStore } from '@/stores/ui-store';

export const Route = createFileRoute('/program/wizard')({
  component: ProgramWizardPage,
});

const STEP_LABELS = [
  'Set Your Goals',
  'Choose Your Schedule',
  'Training Styles',
  'Exercise Preferences',
  'Favorite Activities',
  'Meet Your Coach',
];

// Map communication style to PersonaTone
const TONE_MAP: Record<string, PersonaTone> = {
  encouraging: PersonaTone.SUPPORTIVE,
  drill_sergeant: PersonaTone.DRILL_SERGEANT,
  scientific: PersonaTone.ANALYTICAL,
  casual: PersonaTone.MOTIVATIONAL,
};

function ProgramWizardPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(0);
  const createProgram = useCreateProgram();
  const { addToast } = useUIStore();
  
  const {
    goals,
    isGoalsValid,
    splitPreference,
    daysPerWeek,
    disciplines,
    isDisciplinesValid,
    movementRules,
    enjoyableActivities,
    communicationStyle,
    pushIntensity,
    durationWeeks,
    reset,
  } = useProgramWizardStore();

  // Reset wizard state on mount
  useEffect(() => {
    reset();
  }, [reset]);

  const canProceed = (): boolean => {
    switch (currentStep) {
      case 0: // Goals
        return isGoalsValid();
      case 1: // Split
        return splitPreference !== null;
      case 2: // Disciplines (optional, but must complete if started)
        // If user hasn't allocated any dollars, they can skip
        // If they started allocating, they must allocate all 10
        return disciplines.length === 0 || isDisciplinesValid();
      case 3: // Movements (optional)
        return true;
      case 4: // Activities (optional)
        return true;
      case 5: // Coach
        return true;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (currentStep < STEP_LABELS.length - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleSubmit = async () => {
    // Build the program create payload
    const payload: ProgramCreate = {
      goals: goals,
      duration_weeks: durationWeeks,
      split_template: splitPreference || SplitTemplate.FULL_BODY,
      days_per_week: daysPerWeek,  // User's training frequency preference
      // progression_style is now auto-assigned by backend based on experience level
      persona_tone: TONE_MAP[communicationStyle] || PersonaTone.SUPPORTIVE,
      persona_aggression: pushIntensity as PersonaAggression,
      disciplines: disciplines.length > 0 ? disciplines : undefined,  // Training style preferences
      movement_rules: movementRules.length > 0 ? movementRules : undefined,
      enjoyable_activities: enjoyableActivities.length > 0 ? enjoyableActivities : undefined,
    };

    try {
      const program = await createProgram.mutateAsync(payload);
      reset();
      // Navigate to the new program detail page
      navigate({ 
        to: '/program/$programId', 
        params: { programId: String(program.id) } 
      });
    } catch (error) {
      console.error('Failed to create program:', error);
      const err = error as AxiosError<unknown>;
      const data = err.response?.data as { detail?: unknown } | string | undefined;
      const detail = typeof data === 'object' && data !== null ? data.detail : undefined;

      if (Array.isArray(detail)) {
        const messages = detail.map((d: { loc?: string[]; msg?: string }) => {
          const field = d.loc?.slice(1)?.join('.') || 'unknown field';
          return `${field}: ${d.msg}`;
        });
        addToast({
          type: 'error',
          message: `Validation failed: ${messages.join(' | ')}`,
        });
      } else if (typeof detail === 'string') {
        addToast({ type: 'error', message: detail });
      } else if (typeof data === 'string') {
        addToast({ type: 'error', message: data });
      } else if (data && typeof data === 'object') {
        addToast({ type: 'error', message: JSON.stringify(data) });
      } else if (!err.response) {
        addToast({
          type: 'error',
          message: 'Network error while creating program. Please check that the server is running.',
        });
      } else {
        addToast({
          type: 'error',
          message: 'Failed to create program. Please check your selections and try again.',
        });
      }
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return <GoalsStep />;
      case 1:
        return <SplitStep />;
      case 2:
        return <DisciplinesStep />;
      case 3:
        return <MovementsStep />;
      case 4:
        return <ActivitiesStep />;
      case 5:
        return <CoachStep />;
      default:
        return null;
    }
  };

  return (
    <WizardContainer
      currentStep={currentStep}
      totalSteps={STEP_LABELS.length}
      stepLabels={STEP_LABELS}
      onNext={handleNext}
      onBack={handleBack}
      onSubmit={handleSubmit}
      canProceed={canProceed()}
      isSubmitting={createProgram.isPending}
    >
      {renderStep()}
    </WizardContainer>
  );
}

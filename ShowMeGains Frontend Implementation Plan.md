# ShowMeGains Frontend Implementation Plan
## React + TypeScript + Vite Web UI
# Problem Statement
ShowMeGains has a complete FastAPI backend with LLM-powered session adaptation, program generation, and workout logging. A web frontend is needed to expose these capabilities with a cohesive, performant UI that prioritizes real-time feedback (SSE streaming) and intuitive user workflows.
# Current State
* Backend: FastAPI with 6 core services, 4 REST routers, 60+ unit tests, 5 integration tests
* Tech Stack: Python 3.11+, FastAPI, SQLite, Ollama (local LLM)
* MVP: Single-user (hardcoded user_id=1), no authentication
* Streaming: SSE implemented for session adaptation with incremental LLM output
* No frontend exists
# Design Principles & Global Rules
## Color & Contrast System
* **Primary Brand**: Vibrant teal/cyan (#06B6D4) for calls-to-action, program progress, achievement states
* **Secondary**: Deep slate (#1E293B) for backgrounds, typography
* **Accent**: Amber (#F59E0B) for warnings, deload indicators, recovery alerts
* **Success**: Emerald (#10B981) for completed sessions, PRs, positive metrics
* **Destructive**: Rose (#F43F5E) for danger states, session cancellation
* **Background Hierarchy**:
    * Primary BG: White (#FFFFFF) or near-black (#0F172A) in dark mode
    * Secondary BG: Light gray (#F1F5F9) or slate-900 (#111827)
    * Tertiary BG: Medium gray (#E2E8F0) or slate-800 (#1E293B)
* **Text Contrast Minimums** (WCAG AA):
    * Heading (H1-H3): White text on primary brand = 11.5:1 contrast (✓)
    * Body text: Slate-900 on white = 16.5:1 contrast (✓)
    * Body text: White on slate-900 = 16.5:1 contrast (✓)
    * Secondary text (muted): Slate-600 on white = 5.2:1 contrast (✓)
## Typography System
* **Headings**: Inter 700 (bold) — clean, geometric
    * H1 (page titles): 32px line-height 1.2
    * H2 (section headers): 24px line-height 1.3
    * H3 (subsections): 18px line-height 1.4
* **Body**: Inter 400 (regular) — 16px line-height 1.6 for readability
* **Small/labels**: Inter 500 (medium) — 12px line-height 1.5
* **Monospace** (metrics, duration): Fira Code 400 — 13px, used only for numerical data
## Button System (Unified Design)
* **Base Rules**:
    * Height: 40px (primary), 32px (secondary), 28px (compact)
    * Border-radius: 8px
    * Transition: all 200ms ease-in-out (color, shadow, transform)
    * Font: Inter 500, 14px, uppercase tracking +0.5px
    * Minimum tap target: 44x44px (mobile accessibility)
* **Primary Button** (main actions—create program, adapt session, log workout):
    * BG: Teal (#06B6D4), Text: White
    * Hover: Darker teal (#0891B2), shadow elevation +2px
    * Active: Slate (#1E293B) background, white text
    * Disabled: Gray (#9CA3AF), text slate-500
    * Icon: Centered left, 4px margin-right
* **Secondary Button** (alternatives, back, cancel):
    * BG: Transparent, Border: 2px slate-300, Text: slate-900
    * Hover: BG slate-100, border slate-400
    * Active: BG slate-200
    * Disabled: Border gray-300, text gray-400
* **Danger Button** (delete, cancel session):
    * BG: Rose (#F43F5E), Text: White
    * Hover: Darker rose (#E11D48)
    * Active: Dark rose (#BE123C)
* **Ghost Button** (low-priority, accept/dismiss):
    * BG: Transparent, Text: teal-600
    * Hover: BG teal-50
    * Active: BG teal-100
* **Button Group**:
    * Gap: 8px between buttons
    * Horizontal layout: justify-between for full-width groups
    * Stack vertically on mobile (<640px)
## Modal/Dialog System
* **Overlay**: Semi-transparent dark (#000000 at 40% opacity) — appears instantly
* **Modal Window**:
    * BG: White (#FFFFFF)
    * Border-radius: 12px
    * Shadow: `0 20px 25px -5px rgba(0,0,0,0.1)` (elevation)
    * Padding: 24px (desktop), 16px (mobile)
    * Max-width: 500px (standard), 700px (form-heavy)
    * Entrance animation: Scale 0.95 → 1.0 with fade-in (150ms cubic-bezier(0.4,0,0.2,1))
    * Exit animation: Scale 1.0 → 0.95 with fade-out (100ms)
* **Close Button** (top-right, always present): X icon, 32x32px, gray-400 hover
* **Footer**: Sticky button row (primary + secondary), separator line above at gray-200
## Page Transition System
* **Entrance**: Fade-in (0–150ms) + subtle Y-axis slide (+8px from bottom)
* **Exit**: Fade-out (0–100ms) + Y-axis slide (-8px to top)
* **Curve**: cubic-bezier(0.4,0,0.2,1) (material design standard)
* **No scroll restoration** on navigation; preserve scroll position on back
* **Route hierarchy**: Deeper routes slide from right; pop-ups center-scale
## Form System
* **Input Fields**:
    * Height: 40px
    * Padding: 10px 12px
    * Border: 1px solid #D1D5DB (gray-300), border-radius 6px
    * Focus: Border teal-500, shadow `0 0 0 3px rgba(6,182,212,0.1)` (teal glow)
    * Disabled: BG gray-100, text gray-500, border gray-200
    * Error state: Border rose-500, bottom 2px rose accent
* **Labels**:
    * Font: Inter 500, 12px, slate-700
    * Margin-bottom: 6px
    * Required indicator: Red asterisk (*) after label
* **Help Text**: Inter 400, 12px, slate-600, margin-top 4px
* **Error Messages**: Rose-600, 12px, icon (!) left-aligned, appears with fade-in
* **Validation Feedback**: Real-time after blur, debounced 200ms during typing
## Card/Container System
* **Base Card**:
    * BG: White (#FFFFFF)
    * Border-radius: 8px
    * Border: 1px solid gray-200
    * Padding: 16px (standard), 12px (compact)
    * Hover: Shadow elevation +1px, border gray-300 (optional for clickable)
    * Transition: all 200ms ease
* **Alert/Status Card**:
    * Success: BG emerald-50, border emerald-200, icon + text emerald-900
    * Warning: BG amber-50, border amber-200, icon + text amber-900
    * Error: BG rose-50, border rose-200, icon + text rose-900
    * Info: BG blue-50, border blue-200, icon + text blue-900
* **Data Card** (metrics, session info):
    * Small stat: 2-column grid on desktop, stack on mobile
    * Label: slate-600 12px; value: slate-900 18px bold
    * Divider: vertical (desktop) or horizontal (mobile) gray-200 line
## Loading & Skeleton States
* **Skeleton Pulse**: BG gray-200, animate pulse 2s ease-in-out (opacity 0.5–1.0)
* **Spinner**: Teal-600 ring, 24px diameter, rotate 360deg over 1s linear
* **Progress Bar**: BG gray-200, fill teal-500, height 4px, border-radius 2px
* **Streaming Feedback**: Animated dots ("…" → animation), gray-600 text, fade-in per chunk
## Spacing System (8px base grid)
* xs: 4px
* sm: 8px
* md: 16px
* lg: 24px
* xl: 32px
* 2xl: 48px
* Use consistently across padding, margins, gaps
## Icon System
* Source: Heroicons (24x24px default, 16x16px compact)
* Colors: Inherit text color or explicit slate-600, teal-600, rose-600
* Stroke-width: 2px for clarity at small sizes
* No shadow or layering unless specifically highlighted
## Accessibility Baseline
* **Focus Indicators**: Always visible (never remove outline), 2px teal ring with 2px offset
* **Color Alone**: Never convey info via color only (use icons + text)
* **Skip Links**: Invisible skip-to-main navigation (visible on focus)
* **ARIA Labels**: Buttons/icons with no visible text must have aria-label
* **Semantic HTML**: Use <button>, <form>, <nav>, <main>, <article> correctly
* **Keyboard Navigation**: Tab order follows logical left-to-right, top-to-bottom
* **Motion**: Respect prefers-reduced-motion (fade only, no translate/scale)
## Dark Mode (Future, but plan for it now)
* All colors already defined with light + dark counterparts
* Use CSS custom properties: `--color-primary-bg: #FFFFFF`
* Toggle in settings; persist to localStorage
# Proposed Architecture
## Directory Structure
```warp-runnable-command
frontend/
├── src/
│   ├── components/
│   │   ├── common/           # Global, reusable components
│   │   │   ├── Button.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Form/
│   │   │   │   ├── Input.tsx
│   │   │   │   ├── Label.tsx
│   │   │   │   ├── Select.tsx
│   │   │   ├── Alert.tsx
│   │   │   ├── Spinner.tsx
│   │   │   ├── Skeleton.tsx
│   │   │   └── Icon.tsx
│   │   ├── features/         # Feature-specific components
│   │   │   ├── program/
│   │   │   │   ├── ProgramCard.tsx
│   │   │   │   ├── GoalSelector.tsx
│   │   │   │   └── SplitTemplateSelect.tsx
│   │   │   ├── daily/
│   │   │   │   ├── DailyPlanCard.tsx
│   │   │   │   ├── SessionDetails.tsx
│   │   │   │   ├── AdaptationForm.tsx
│   │   │   │   └── StreamingFeedback.tsx
│   │   │   ├── logging/
│   │   │   │   ├── WorkoutLogForm.tsx
│   │   │   │   ├── SorenessInput.tsx
│   │   │   │   └── RecoveryLogger.tsx
│   │   │   └── settings/
│   │   │       ├── UserPreferences.tsx
│   │   │       └── MovementRules.tsx
│   │   └── layout/
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       ├── MainLayout.tsx
│   │       └── PageTransition.tsx
│   ├── hooks/                # Custom React hooks
│   │   ├── useApi.ts         # Wrapper around fetch for API calls
│   │   ├── useSse.ts         # Hook for SSE streaming
│   │   ├── useLocalStorage.ts
│   │   ├── useMediaQuery.ts  # Responsive breakpoints
│   │   ├── useAsync.ts       # Async state management
│   │   └── useAuth.ts        # Future: JWT auth
│   ├── api/
│   │   ├── client.ts         # Axios/fetch instance with base URL
│   │   ├── programs.ts       # Program endpoints
│   │   ├── daily.ts          # Daily plan endpoints
│   │   ├── logging.ts        # Workout/recovery logging endpoints
│   │   └── settings.ts       # User settings endpoints
│   ├── types/
│   │   ├── api.ts            # All API response/request types
│   │   ├── domain.ts         # Business logic types (Program, Session, etc.)
│   │   └── ui.ts             # UI state types
│   ├── store/
│   │   ├── programStore.ts   # TanStack Query queries for programs
│   │   ├── dailyStore.ts     # Daily plan queries
│   │   └── userStore.ts      # User preferences, settings
│   ├── styles/
│   │   ├── globals.css       # Tailwind imports, custom properties, keyframes
│   │   ├── variables.css     # CSS custom properties (colors, spacing, fonts)
│   │   └── animations.css    # Reusable animations (fade, slide, pulse)
│   ├── utils/
│   │   ├── format.ts         # Date, number formatting
│   │   ├── validation.ts     # Form validation (Zod schemas)
│   │   └── constants.ts      # App-wide constants (API base URL, etc.)
│   ├── pages/                # Page-level components (routes)
│   │   ├── Home.tsx
│   │   ├── Onboarding.tsx
│   │   ├── DailyPlan.tsx
│   │   ├── ProgramHistory.tsx
│   │   ├── Settings.tsx
│   │   └── NotFound.tsx
│   ├── App.tsx               # Root component with routing
│   └── main.tsx              # Vite entry point
├── public/                   # Static assets (logo, favicon)
├── tests/
│   ├── components/           # Component tests (Vitest + RTL)
│   ├── hooks/                # Hook tests
│   ├── api/                  # API client tests (MSW mocks)
│   └── utils/                # Utility function tests
├── .env.example              # Environment template
├── vite.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── vitest.config.ts
└── package.json
```
## Tech Stack Details
* **Routing**: TanStack Router (modern, type-safe, file-based optional)
* **State Management**: TanStack Query v5 for server state; Zustand for UI state (sidebar toggle, theme)
* **Forms**: React Hook Form + Zod for validation
* **Styling**: Tailwind CSS (pre-configured with design tokens)
* **HTTP Client**: Fetch API with custom wrapper for SSE support
* **Testing**: Vitest (Jest-compatible, faster) + React Testing Library + MSW for API mocking
* **Build**: Vite (lightning-fast HMR, sub-second rebuilds)
## Implementation Phases
### Phase 1: Foundation (Week 1)
1. **Project Setup**
    * Initialize Vite project with React + TypeScript template
    * Configure Tailwind CSS with custom design tokens (colors, spacing, fonts)
    * Set up routing (TanStack Router)
    * Configure environment variables (.env.local for API base URL)
    * Commit: "chore: initialize react frontend with vite and tailwind"
2. **Global Components Library** (Design system foundation)
    * Button.tsx (all variants: primary, secondary, danger, ghost, sizes)
    * Card.tsx (base, alert variants)
    * Modal.tsx (reusable dialog wrapper)
    * Form components: Input, Label, Select, Checkbox, Radio
    * Alert.tsx (success, warning, error, info)
    * Spinner.tsx, Skeleton.tsx
    * Commit: "feat: implement global component library matching design system"
3. **Layout & Navigation**
    * MainLayout.tsx (header + sidebar + main content)
    * Header.tsx (logo, nav links, user menu placeholder)
    * Sidebar.tsx (navigation: Daily Plan, Programs, Logging, Settings)
    * PageTransition.tsx (fade/slide animations)
    * Commit: "feat: implement base layout and navigation"
4. **API Client & Hooks**
    * api/client.ts (fetch wrapper with base URL, error handling)
    * hooks/useApi.ts (generic hook for GET/POST/PUT)
    * hooks/useSse.ts (hook for SSE streaming)
    * types/api.ts (TypeScript interfaces for all endpoints)
    * Commit: "feat: implement api client and core hooks"
5. **Testing Setup**
    * Configure Vitest, React Testing Library, MSW
    * Write first component test (Button.tsx)
    * Create API mock handlers for all endpoints
    * Commit: "chore: configure testing infrastructure"
### Phase 2: Core Features (Week 2)
1. **Home & Onboarding**
    * Home.tsx (landing page, quick stats, next session CTA)
    * Onboarding.tsx (create program flow with form validation)
    * GoalSelector.tsx (weight 3 goals summing to 10)
    * SplitTemplateSelect.tsx (Upper/Lower, PPL, Full Body, Hybrid)
    * ProgressionStyleSelect.tsx (Single, Double, Paused, Build-to-Drop)
    * API: POST /programs with ProgramService integration
    * Tests: Form validation, goal weight validation, API integration
    * Commit: "feat: implement program creation onboarding flow"
2. **Daily Plan View**
    * DailyPlan.tsx (page showing today's session or rest day)
    * SessionDetails.tsx (display warmup → main → accessory → finisher → cooldown)
    * DailyPlanCard.tsx (quick overview card)
    * Duration breakdown visualization (pie chart or horizontal bar)
    * API: GET /days/{date}/plan
    * Tests: Session rendering, rest day handling, duration display
    * Commit: "feat: implement daily plan view"
3. **Session Adaptation (Real-time Streaming)**
    * AdaptationForm.tsx (constraints: excluded movements, time available, preference, focus)
    * StreamingFeedback.tsx (real-time LLM output with recovery score display)
    * Custom hook: useSse() for managing EventSource and SSE parsing
    * Recovery score visualization (gauge component)
    * Streaming feedback list (appending chunks as they arrive)
    * API: POST /days/{date}/adapt/stream (SSE)
    * Tests: SSE parsing, error recovery, graceful stream termination
    * Commit: "feat: implement real-time session adaptation with SSE streaming"
4. **Workout Logging**
    * WorkoutLogForm.tsx (exercise, sets, reps, weight, RPE, notes)
    * SorenessInput.tsx (body part soreness scale 1-5, multi-select)
    * RecoveryLogger.tsx (sleep score, HRV, readiness, notes)
    * API: POST /logs/workouts, POST /logs/soreness, POST /logs/recovery
    * Tests: Form validation, multi-set entry, auto-calculation (e1RM)
    * Commit: "feat: implement workout and recovery logging"
### Phase 3: Polish & Scaling (Week 3)
1. **Settings & User Preferences**
    * Settings.tsx (user preferences page)
    * UserPreferences.tsx (persona, units (lbs/kg), e1RM formula, coach tone)
    * MovementRules.tsx (exclude/substitute/prefer movement management)
    * API: PUT /settings, POST/DELETE /settings/movement-rules
    * Tests: Preference persistence, rule creation/deletion
    * Commit: "feat: implement user settings and movement rules"
2. **Program History & Analytics**
    * ProgramHistory.tsx (list of past/current programs)
    * ProgramCard.tsx (program overview, microcycle progress)
    * MetricsView.tsx (e1RM trends, PSI by pattern, volume trends)
    * API: GET /programs, GET /programs/{id}
    * Tests: Program listing, data visualization
    * Commit: "feat: implement program history and basic analytics"
3. **Error Handling & Offline Support**
    * Global error boundary (graceful failure UI)
    * Retry logic for failed API calls (exponential backoff)
    * Offline detection (notify user, queue actions)
    * API: Error responses with user-friendly messages
    * Tests: Error boundary rendering, retry behavior
    * Commit: "feat: implement error handling and offline resilience"
4. **Performance Optimization**
    * Lazy-load routes (code splitting)
    * Memoize expensive components
    * Debounce form inputs
    * Image optimization (favicon, logo)
    * Bundle analysis (check Vite output)
    * Tests: Load time baselines
    * Commit: "perf: optimize bundle size and rendering performance"
### Phase 4: Mobile Preparation & Refinement (Week 4)
1. **Responsive Design Audit**
    * Test all pages at 375px (iPhone SE), 768px (iPad), 1440px (desktop)
    * Stack components vertically on mobile
    * Touch targets ≥44x44px
    * Modal max-width responsive (500px desktop, 90vw mobile)
    * Tests: Responsive visual regression tests
    * Commit: "feat: ensure full responsive design across breakpoints"
2. **Mobile-First Refinements**
    * Bottom sheet alternative for modals on mobile
    * Swipe gestures for navigation (optional, low priority)
    * Larger touch targets for buttons on mobile
    * Full-screen forms on mobile for focus
    * Commit: "feat: enhance mobile ux with bottom sheets and larger touch targets"
3. **Documentation & Handoff**
    * Storybook setup (optional, but useful for component library)
    * README with setup, environment variables, running locally
    * Contributing guide for future mobile team
    * API documentation (OpenAPI from backend)
    * Commit: "docs: add storybook and comprehensive readme"
4. **Launch Checklist**
    * SEO: Meta tags, favicon, Open Graph (if serving web)
    * Analytics: Google Analytics or Posthog (optional)
    * Error tracking: Sentry (optional, optional for MVP)
    * Performance monitoring: Web Vitals
    * Security: CSP headers, XSS protection
    * Tests: 80%+ coverage for critical paths
    * Commit: "chore: add seo, analytics, and security headers"
## Key Dependencies
* `react@latest`, `react-dom@latest`
* `typescript@latest`
* `@tanstack/react-query@latest` (server state)
* `@tanstack/react-router@latest` (routing)
* `react-hook-form` (forms)
* `zod` (validation)
* `zustand` (UI state)
* `tailwindcss@latest`, `@tailwindcss/forms`
* `@heroicons/react` (icons)
* `axios` or `fetch` (HTTP) — use fetch + wrapper
* Dev: `vitest`, `@testing-library/react`, `@testing-library/user-event`, `msw`
## Success Criteria
* All pages render with zero console errors
* Daily plan loads <500ms (with TanStack Query caching)
* Session adaptation streams at 200-500ms chunk intervals (real-time feel)
* All forms validate with helpful error messages
* Mobile responsive at 375px, 768px, 1440px breakpoints
* Component library is reusable across all pages (no one-off styles)
* 80%+ test coverage for critical paths (onboarding, daily plan, logging)
* Meets WCAG AA accessibility standards
* Build size <300KB gzipped (core bundle)
## Known Constraints & Future Work
* **Authentication**: Currently single-user; JWT auth integration needed for multi-user SaaS (Phase 5)
* **Mobile Native**: React Native from shared logic (Phase 5+)
* **Offline Sync**: Service Worker caching + IndexedDB (Phase 5, optional)
* **Real-time Sync**: WebSocket for live program updates (Phase 5, if needed)
* **Admin Panel**: Heuristic management UI (Phase 5+)
# Design Tokens (Tailwind Config)
## Colors
* Primary: teal-500 (#06B6D4) → override in tailwind.config.ts
* Secondary: slate-600 (#475569)
* Accent: amber-500 (#F59E0B)
* Success: emerald-500 (#10B981)
* Destructive: rose-500 (#F43F5E)
* Neutral: gray/slate grays
## Spacing
* Use 8px base grid (xs=4, sm=8, md=16, lg=24, xl=32, 2xl=48)
* Tailwind defaults (1=4px) are close; extend if needed
## Typography
* Font stack: `['Inter', 'system-ui', sans-serif]`
* Weights: 400 (regular), 500 (medium), 700 (bold)
* Size scale: 12, 14, 16, 18, 24, 32px
## Breakpoints
* sm: 640px (mobile)
* md: 768px (tablet)
* lg: 1024px (desktop)
* xl: 1280px (wide desktop)

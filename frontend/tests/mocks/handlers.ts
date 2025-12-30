import { http, HttpResponse } from 'msw'

const API_BASE = 'http://localhost:8000'

export const handlers = [
  // Programs
  http.get(`${API_BASE}/programs`, () => {
    return HttpResponse.json([
      {
        id: 1,
        user_id: 1,
        program_start_date: '2024-01-01',
        duration_weeks: 8,
        goal_1: 'strength',
        goal_2: 'hypertrophy',
        goal_3: 'endurance',
        goal_weight_1: 5,
        goal_weight_2: 3,
        goal_weight_3: 2,
        split_template: 'UPPER_LOWER',
        progression_style: 'DOUBLE',
        deload_every_n_microcycles: 4,
        is_active: true,
      },
    ])
  }),

  http.post(`${API_BASE}/programs`, async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      id: 1,
      user_id: 1,
      ...body,
      created_at: new Date().toISOString(),
    })
  }),

  // Daily Plan
  http.get(`${API_BASE}/days/:date/plan`, ({ params }) => {
    return HttpResponse.json({
      plan_date: params.date,
      session: null,
      is_rest_day: true,
      coach_message: 'Rest day - take it easy and recover!',
    })
  }),

  // Logging
  http.post(`${API_BASE}/logs/workouts`, async ({ request }) => {
    const body = await request.json()
    return HttpResponse.json({
      workout_log: {
        id: 1,
        user_id: 1,
        ...body,
        created_at: new Date().toISOString(),
      },
      pattern_exposures_created: 0,
      psi_updates: {},
    })
  }),

  // Settings
  http.get(`${API_BASE}/settings`, () => {
    return HttpResponse.json({
      id: 1,
      user_id: 1,
      active_e1rm_formula: 'epley',
      use_metric: true,
    })
  }),

  http.get(`${API_BASE}/settings/movements`, () => {
    return HttpResponse.json({
      movements: [
        { id: 1, name: 'Barbell Back Squat', pattern: 'squat', primary_region: 'lower_body' },
        { id: 2, name: 'Bench Press', pattern: 'push', primary_region: 'upper_body' },
        { id: 3, name: 'Deadlift', pattern: 'hinge', primary_region: 'lower_body' },
      ],
      total: 3,
    })
  }),

  // Health check
  http.get(`${API_BASE}/health`, () => {
    return HttpResponse.json({ status: 'healthy' })
  }),
]

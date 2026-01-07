import { lazy, Suspense } from 'react'
import {
  createRouter,
  createRootRoute,
  createRoute,
  Outlet,
} from '@tanstack/react-router'
import { MainLayout } from './components/layout'
import { Spinner } from './components/common'

// Lazy load pages for code splitting
const Home = lazy(() => import('./pages/Home'))
const DailyPlan = lazy(() => import('./pages/DailyPlan'))
const Onboarding = lazy(() => import('./pages/Onboarding'))
const Logging = lazy(() => import('./pages/Logging'))
const Settings = lazy(() => import('./pages/Settings'))
const Programs = lazy(() => import('./pages/Programs'))

// Loading fallback
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-[400px]">
    <Spinner size="lg" />
  </div>
)

// Wrap component with Suspense
const withSuspense = (Component: React.LazyExoticComponent<React.FC>) => () => (
  <Suspense fallback={<PageLoader />}>
    <Component />
  </Suspense>
)

// Root layout route
const rootRoute = createRootRoute({
  component: () => (
    <MainLayout>
      <Outlet />
    </MainLayout>
  ),
})

// Home route
const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: withSuspense(Home),
})

// Daily Plan route with optional date parameter
const dailyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/daily',
  component: withSuspense(DailyPlan),
})

// Daily Plan with specific date
const dailyDateRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/daily/$date',
  component: withSuspense(DailyPlan),
})

// Programs route
const programsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/programs',
  component: withSuspense(Programs),
})

// Onboarding route
const onboardingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/onboarding',
  component: withSuspense(Onboarding),
})

// Logging route
const loggingRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/logging',
  component: withSuspense(Logging),
})

// Settings route
const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: withSuspense(Settings),
})

// 404 Not Found route
const notFoundRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '*',
  component: () => (
    <div className="text-center py-8">
      <h1 className="text-2xl font-bold">404 - Page Not Found</h1>
      <p className="text-secondary-600 mt-2">
        The page you're looking for doesn't exist.
      </p>
    </div>
  ),
})

// Build the route tree
const routeTree = rootRoute.addChildren([
  homeRoute,
  dailyRoute,
  dailyDateRoute,
  programsRoute,
  onboardingRoute,
  loggingRoute,
  settingsRoute,
  notFoundRoute,
])

// Create the router instance
export const router = createRouter({ routeTree })

// Type declaration for router
declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

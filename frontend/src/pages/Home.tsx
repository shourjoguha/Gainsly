import React from 'react'
import { Button, Card, CardTitle, CardDescription, CardContent, CardFooter } from '../components/common'
import { CalendarDaysIcon, ChartBarIcon, PlusIcon } from '@heroicons/react/24/outline'

const Home: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-secondary-900 mb-2">
          Welcome to ShowMeGains
        </h1>
        <p className="text-secondary-600 max-w-xl mx-auto">
          Your AI-powered workout coach. Create adaptive programs, track your progress, 
          and get personalized daily sessions based on your recovery.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mb-8">
        <Card hoverable onClick={() => window.location.href = '/daily'}>
          <CardContent className="flex items-start gap-4">
            <div className="p-3 bg-primary-100 rounded-lg">
              <CalendarDaysIcon className="w-6 h-6 text-primary-600" />
            </div>
            <div>
              <CardTitle className="text-base">Today's Session</CardTitle>
              <CardDescription>View and adapt your workout for today</CardDescription>
            </div>
          </CardContent>
        </Card>

        <Card hoverable onClick={() => window.location.href = '/programs'}>
          <CardContent className="flex items-start gap-4">
            <div className="p-3 bg-success-100 rounded-lg">
              <ChartBarIcon className="w-6 h-6 text-success-600" />
            </div>
            <div>
              <CardTitle className="text-base">My Programs</CardTitle>
              <CardDescription>View progress and manage programs</CardDescription>
            </div>
          </CardContent>
        </Card>

        <Card hoverable onClick={() => window.location.href = '/onboarding'}>
          <CardContent className="flex items-start gap-4">
            <div className="p-3 bg-accent-100 rounded-lg">
              <PlusIcon className="w-6 h-6 text-accent-600" />
            </div>
            <div>
              <CardTitle className="text-base">New Program</CardTitle>
              <CardDescription>Create a new training program</CardDescription>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Getting Started */}
      <Card>
        <CardContent>
          <h2 className="text-xl font-bold text-secondary-900 mb-4">Getting Started</h2>
          <ol className="list-decimal list-inside space-y-2 text-secondary-700">
            <li>Create a program with your 3 weighted goals (strength, hypertrophy, endurance, etc.)</li>
            <li>Choose your split template (Upper/Lower, PPL, Full Body, or Hybrid)</li>
            <li>Each day, check your session and adapt it based on how you feel</li>
            <li>Log your workouts and recovery to help the AI optimize your training</li>
          </ol>
        </CardContent>
        <CardFooter>
          <Button onClick={() => window.location.href = '/onboarding'}>
            Create Your First Program
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}

export default Home

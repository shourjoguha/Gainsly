import { MainLayout } from './components/layout'
import { Home } from './pages'

function App() {
  // Simple routing based on pathname
  // This will be replaced with TanStack Router in next iteration
  const path = window.location.pathname

  const renderPage = () => {
    switch (path) {
      case '/':
        return <Home />
      case '/daily':
        return <div className="text-center py-8"><h1 className="text-2xl font-bold">Daily Plan</h1><p className="text-secondary-600">Coming in Phase 2</p></div>
      case '/programs':
        return <div className="text-center py-8"><h1 className="text-2xl font-bold">Programs</h1><p className="text-secondary-600">Coming in Phase 2</p></div>
      case '/logging':
        return <div className="text-center py-8"><h1 className="text-2xl font-bold">Logging</h1><p className="text-secondary-600">Coming in Phase 2</p></div>
      case '/settings':
        return <div className="text-center py-8"><h1 className="text-2xl font-bold">Settings</h1><p className="text-secondary-600">Coming in Phase 3</p></div>
      case '/onboarding':
        return <div className="text-center py-8"><h1 className="text-2xl font-bold">Create Program</h1><p className="text-secondary-600">Coming in Phase 2</p></div>
      default:
        return <div className="text-center py-8"><h1 className="text-2xl font-bold">404 - Page Not Found</h1></div>
    }
  }

  return (
    <MainLayout currentPath={path}>
      {renderPage()}
    </MainLayout>
  )
}

export default App

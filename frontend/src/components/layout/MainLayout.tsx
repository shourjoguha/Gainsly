import React, { useState } from 'react'
import { clsx } from 'clsx'
import { useRouterState } from '@tanstack/react-router'
import Header from './Header'
import Sidebar from './Sidebar'

interface MainLayoutProps {
  children: React.ReactNode
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const routerState = useRouterState()
  const currentPath = routerState.location.pathname

  return (
    <div className="h-screen w-full flex flex-col bg-secondary-50 overflow-hidden">
      {/* Skip to main content link for accessibility */}
      <a
        href="#main-content"
        className="skip-to-main"
      >
        Skip to main content
      </a>

      {/* Header - Stays at top */}
      <Header onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />

      {/* Content Area - Flex Row for Sidebar + Main */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Static on desktop, drawer on mobile */}
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          currentPath={currentPath}
        />

        {/* Main content - Scrollable area */}
        <main
          id="main-content"
          className={clsx(
            'flex-1',
            'overflow-y-auto',
            'bg-secondary-50',
            'w-full',
            'relative' // Ensure context
          )}
        >
          <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}

export default MainLayout

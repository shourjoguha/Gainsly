import React, { useState } from 'react'
import { clsx } from 'clsx'
import Header from './Header'
import Sidebar from './Sidebar'

interface MainLayoutProps {
  children: React.ReactNode
  currentPath?: string
}

const MainLayout: React.FC<MainLayoutProps> = ({ children, currentPath }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-secondary-50">
      {/* Skip to main content link for accessibility */}
      <a
        href="#main-content"
        className="skip-to-main"
      >
        Skip to main content
      </a>

      {/* Header */}
      <Header onMenuToggle={() => setSidebarOpen(!sidebarOpen)} />

      {/* Sidebar */}
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        currentPath={currentPath}
      />

      {/* Main content */}
      <main
        id="main-content"
        className={clsx(
          'pt-16', // Account for fixed header
          'lg:pl-64', // Account for sidebar on large screens
          'min-h-screen'
        )}
      >
        <div className="p-4 sm:p-6 lg:p-8 animate-fade-in">
          {children}
        </div>
      </main>
    </div>
  )
}

export default MainLayout

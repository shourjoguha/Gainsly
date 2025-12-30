import React from 'react'
import { clsx } from 'clsx'
import { Bars3Icon, UserCircleIcon } from '@heroicons/react/24/outline'

interface HeaderProps {
  onMenuToggle?: () => void
  className?: string
}

const Header: React.FC<HeaderProps> = ({ onMenuToggle, className }) => {
  return (
    <header
      className={clsx(
        'fixed top-0 left-0 right-0 z-40',
        'h-16 px-4 sm:px-6',
        'bg-white border-b border-secondary-200',
        'flex items-center justify-between',
        className
      )}
    >
      {/* Left side: Menu button (mobile) + Logo */}
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className={clsx(
            'lg:hidden p-2 -ml-2',
            'rounded-lg text-secondary-600',
            'hover:bg-secondary-100',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500'
          )}
          aria-label="Toggle menu"
        >
          <Bars3Icon className="w-6 h-6" />
        </button>

        {/* Logo */}
        <a
          href="/"
          className="flex items-center gap-2 text-secondary-900 hover:text-primary-600 transition-colors"
        >
          <svg
            className="w-8 h-8 text-primary-500"
            viewBox="0 0 32 32"
            fill="currentColor"
          >
            <path d="M16 2L4 8v16l12 6 12-6V8L16 2zm0 4l8 4v8l-8 4-8-4v-8l8-4z" />
            <circle cx="16" cy="16" r="4" />
          </svg>
          <span className="text-xl font-bold tracking-tight hidden sm:block">
            ShowMeGains
          </span>
        </a>
      </div>

      {/* Center: Quick stats or breadcrumb (expandable) */}
      <div className="hidden md:flex items-center gap-4 text-sm text-secondary-600">
        {/* Could show current program info, week number, etc. */}
      </div>

      {/* Right side: User menu */}
      <div className="flex items-center gap-2">
        <button
          className={clsx(
            'flex items-center gap-2 p-2',
            'rounded-lg text-secondary-600',
            'hover:bg-secondary-100',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500'
          )}
          aria-label="User menu"
        >
          <UserCircleIcon className="w-6 h-6" />
          <span className="hidden sm:block text-sm font-medium">User</span>
        </button>
      </div>
    </header>
  )
}

export default Header

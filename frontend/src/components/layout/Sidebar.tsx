import React from 'react'
import { clsx } from 'clsx'
import {
  CalendarDaysIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  Cog6ToothIcon,
  HomeIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

interface NavItem {
  name: string
  href: string
  icon: React.ElementType
  badge?: string | number
}

const navItems: NavItem[] = [
  { name: 'Home', href: '/', icon: HomeIcon },
  { name: 'Today', href: '/daily', icon: CalendarDaysIcon },
  { name: 'Programs', href: '/programs', icon: DocumentTextIcon },
  { name: 'Logging', href: '/logging', icon: ClipboardDocumentListIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
]

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
  currentPath?: string
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose, currentPath = '/' }) => {
  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 lg:hidden animate-fade-in"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          'fixed top-16 bottom-0 left-0 z-40',
          'w-64 bg-white border-r border-secondary-200',
          'transform transition-transform duration-base ease-in-out',
          'lg:translate-x-0',
          isOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        {/* Close button (mobile only) */}
        <button
          onClick={onClose}
          className={clsx(
            'absolute top-4 right-4 lg:hidden',
            'p-2 rounded-lg text-secondary-600',
            'hover:bg-secondary-100',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500'
          )}
          aria-label="Close sidebar"
        >
          <XMarkIcon className="w-5 h-5" />
        </button>

        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {navItems.map((item) => {
            const isActive = currentPath === item.href
            return (
              <a
                key={item.name}
                href={item.href}
                className={clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg',
                  'text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-secondary-600 hover:bg-secondary-100 hover:text-secondary-900'
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <item.icon className="w-5 h-5 flex-shrink-0" />
                <span className="flex-1">{item.name}</span>
                {item.badge && (
                  <span
                    className={clsx(
                      'px-2 py-0.5 rounded-full text-xs font-medium',
                      isActive
                        ? 'bg-primary-100 text-primary-700'
                        : 'bg-secondary-100 text-secondary-600'
                    )}
                  >
                    {item.badge}
                  </span>
                )}
              </a>
            )
          })}
        </nav>

        {/* Bottom section */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-secondary-200">
          <div className="text-xs text-secondary-500 text-center">
            ShowMeGains v1.0.0
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar

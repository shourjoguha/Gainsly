import React from 'react'
import { clsx } from 'clsx'
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  InformationCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline'

type AlertVariant = 'success' | 'warning' | 'error' | 'info'

interface AlertProps {
  variant: AlertVariant
  title?: string
  children: React.ReactNode
  dismissible?: boolean
  onDismiss?: () => void
  className?: string
}

const variantStyles: Record<AlertVariant, string> = {
  success: 'bg-success-50 border-success-200 text-success-900',
  warning: 'bg-accent-50 border-accent-200 text-accent-900',
  error: 'bg-destructive-50 border-destructive-200 text-destructive-900',
  info: 'bg-blue-50 border-blue-200 text-blue-900',
}

const iconMap: Record<AlertVariant, React.ElementType> = {
  success: CheckCircleIcon,
  warning: ExclamationTriangleIcon,
  error: XCircleIcon,
  info: InformationCircleIcon,
}

const iconColors: Record<AlertVariant, string> = {
  success: 'text-success-600',
  warning: 'text-accent-600',
  error: 'text-destructive-600',
  info: 'text-blue-600',
}

const Alert: React.FC<AlertProps> = ({
  variant,
  title,
  children,
  dismissible = false,
  onDismiss,
  className,
}) => {
  const Icon = iconMap[variant]

  return (
    <div
      className={clsx(
        'flex gap-3 p-4 rounded-card border',
        'animate-fade-in',
        variantStyles[variant],
        className
      )}
      role="alert"
    >
      <Icon className={clsx('w-5 h-5 flex-shrink-0 mt-0.5', iconColors[variant])} />
      <div className="flex-1">
        {title && <h4 className="font-medium mb-1">{title}</h4>}
        <div className="text-sm">{children}</div>
      </div>
      {dismissible && onDismiss && (
        <button
          onClick={onDismiss}
          className={clsx(
            'flex-shrink-0 p-1 rounded-full',
            'hover:bg-black/5 transition-colors',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500'
          )}
          aria-label="Dismiss alert"
        >
          <XMarkIcon className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}

export default Alert

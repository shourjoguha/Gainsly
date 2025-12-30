import React from 'react'
import { clsx } from 'clsx'

type CardVariant = 'default' | 'success' | 'warning' | 'error' | 'info'

interface CardProps {
  variant?: CardVariant
  padding?: 'none' | 'sm' | 'md' | 'lg'
  hoverable?: boolean
  className?: string
  children: React.ReactNode
  onClick?: () => void
}

const variantStyles: Record<CardVariant, string> = {
  default: 'bg-white border-secondary-200',
  success: 'bg-success-50 border-success-200',
  warning: 'bg-accent-50 border-accent-200',
  error: 'bg-destructive-50 border-destructive-200',
  info: 'bg-blue-50 border-blue-200',
}

const paddingStyles: Record<string, string> = {
  none: 'p-0',
  sm: 'p-3',
  md: 'p-4',
  lg: 'p-6',
}

const Card: React.FC<CardProps> = ({
  variant = 'default',
  padding = 'md',
  hoverable = false,
  className,
  children,
  onClick,
}) => {
  return (
    <div
      onClick={onClick}
      className={clsx(
        'rounded-card border transition-all duration-base',
        variantStyles[variant],
        paddingStyles[padding],
        hoverable && 'hover:shadow-elevation hover:border-secondary-300 cursor-pointer',
        onClick && 'cursor-pointer',
        className
      )}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => e.key === 'Enter' && onClick() : undefined}
    >
      {children}
    </div>
  )
}

// Subcomponents for card structure
interface CardHeaderProps {
  className?: string
  children: React.ReactNode
}

const CardHeader: React.FC<CardHeaderProps> = ({ className, children }) => (
  <div className={clsx('mb-4', className)}>{children}</div>
)

interface CardTitleProps {
  className?: string
  children: React.ReactNode
}

const CardTitle: React.FC<CardTitleProps> = ({ className, children }) => (
  <h3 className={clsx('text-lg font-bold text-secondary-900', className)}>{children}</h3>
)

interface CardDescriptionProps {
  className?: string
  children: React.ReactNode
}

const CardDescription: React.FC<CardDescriptionProps> = ({ className, children }) => (
  <p className={clsx('text-sm text-secondary-600', className)}>{children}</p>
)

interface CardContentProps {
  className?: string
  children: React.ReactNode
}

const CardContent: React.FC<CardContentProps> = ({ className, children }) => (
  <div className={clsx(className)}>{children}</div>
)

interface CardFooterProps {
  className?: string
  children: React.ReactNode
}

const CardFooter: React.FC<CardFooterProps> = ({ className, children }) => (
  <div className={clsx('mt-4 flex items-center gap-2', className)}>{children}</div>
)

export default Card
export { CardHeader, CardTitle, CardDescription, CardContent, CardFooter }

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
  default: 'bg-dark-850 border-dark-700 shadow-elevation',
  success: 'bg-dark-850 border-neon-green-600 shadow-neon-green-sm',
  warning: 'bg-dark-850 border-neon-amber-600 shadow-neon-amber',
  error: 'bg-dark-850 border-neon-red-600 shadow-neon-red',
  info: 'bg-dark-850 border-neon-cyan-600 shadow-neon-cyan-sm',
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
        hoverable && 'hover:shadow-neon-cyan hover:border-neon-cyan-500 cursor-pointer',
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
  <h3 className={clsx('text-lg font-bold text-white', className)}>{children}</h3>
)

interface CardDescriptionProps {
  className?: string
  children: React.ReactNode
}

const CardDescription: React.FC<CardDescriptionProps> = ({ className, children }) => (
  <p className={clsx('text-sm text-secondary-400', className)}>{children}</p>
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

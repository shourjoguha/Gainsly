import React, { forwardRef } from 'react'
import { clsx } from 'clsx'
import Spinner from './Spinner'

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost'
export type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
  fullWidth?: boolean
  loading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  children: React.ReactNode
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: clsx(
    'bg-primary-500 text-white',
    'hover:bg-primary-600 hover:shadow-elevation',
    'active:bg-secondary-800',
    'disabled:bg-gray-400 disabled:text-gray-600'
  ),
  secondary: clsx(
    'bg-transparent text-secondary-900 border-2 border-secondary-300',
    'hover:bg-secondary-100 hover:border-secondary-400',
    'active:bg-secondary-200',
    'disabled:border-gray-300 disabled:text-gray-400'
  ),
  danger: clsx(
    'bg-destructive-500 text-white',
    'hover:bg-destructive-600',
    'active:bg-destructive-700',
    'disabled:bg-gray-400 disabled:text-gray-600'
  ),
  ghost: clsx(
    'bg-transparent text-primary-600',
    'hover:bg-primary-50',
    'active:bg-primary-100',
    'disabled:text-gray-400'
  ),
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-10 px-4 text-sm',
  lg: 'h-12 px-6 text-base',
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      loading = false,
      leftIcon,
      rightIcon,
      disabled,
      className,
      children,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading

    return (
      <button
        ref={ref}
        disabled={isDisabled}
        className={clsx(
          // Base styles
          'inline-flex items-center justify-center',
          'font-medium uppercase tracking-wide',
          'rounded-btn',
          'transition-all duration-base ease-in-out',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2',
          'min-w-[44px]',
          // Variant styles
          variantStyles[variant],
          // Size styles
          sizeStyles[size],
          // Full width
          fullWidth && 'w-full',
          // Disabled cursor
          isDisabled && 'cursor-not-allowed',
          // Custom className
          className
        )}
        {...props}
      >
        {loading && (
          <span className="mr-2">
            <Spinner size="sm" />
          </span>
        )}
        {!loading && leftIcon && <span className="mr-2">{leftIcon}</span>}
        {children}
        {!loading && rightIcon && <span className="ml-2">{rightIcon}</span>}
      </button>
    )
  }
)

Button.displayName = 'Button'

export default Button

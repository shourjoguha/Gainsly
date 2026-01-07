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
    'bg-gradient-neon-cyan text-black font-semibold',
    'hover:shadow-neon-cyan-lg hover:translate-y-0',
    'active:translate-y-1 active:shadow-neon-cyan-sm',
    'disabled:bg-secondary-700 disabled:text-secondary-500 disabled:shadow-none disabled:translate-y-0'
  ),
  secondary: clsx(
    'bg-dark-850 text-neon-cyan-400 border-2 border-neon-cyan-400',
    'hover:border-neon-cyan-300 hover:shadow-neon-cyan-sm hover:translate-y-0',
    'active:bg-dark-800 active:translate-y-1',
    'disabled:border-secondary-700 disabled:text-secondary-700 disabled:shadow-none disabled:translate-y-0'
  ),
  danger: clsx(
    'bg-gradient-neon-red text-black font-semibold',
    'hover:shadow-neon-red hover:translate-y-0',
    'active:translate-y-1 active:shadow-btn-hover',
    'disabled:bg-secondary-700 disabled:text-secondary-500 disabled:shadow-none disabled:translate-y-0'
  ),
  ghost: clsx(
    'bg-transparent text-neon-cyan-400',
    'hover:text-neon-cyan-300 hover:shadow-neon-cyan-sm',
    'active:text-neon-cyan-500',
    'disabled:text-secondary-700'
  ),
}

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'h-10 px-4 text-sm',
  md: 'h-12 px-6 text-base',
  lg: 'h-14 px-8 text-lg',
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
          'font-semibold uppercase tracking-wider',
          'rounded-btn',
          'transition-all duration-fast ease-in-out',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-neon-cyan-500 focus-visible:ring-offset-2 focus-visible:ring-offset-black',
          'min-w-[44px]',
          'shadow-btn',
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

import React from 'react'
import { clsx } from 'clsx'

interface SkeletonProps {
  className?: string
  variant?: 'text' | 'circular' | 'rectangular'
  width?: string | number
  height?: string | number
  lines?: number
}

const Skeleton: React.FC<SkeletonProps> = ({
  className,
  variant = 'text',
  width,
  height,
  lines = 1,
}) => {
  const baseStyles = 'bg-secondary-200 animate-pulse'

  const variantStyles = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: 'rounded-card',
  }

  const defaultHeights = {
    text: 'h-4',
    circular: 'h-10 w-10',
    rectangular: 'h-20',
  }

  const style: React.CSSProperties = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  }

  if (variant === 'text' && lines > 1) {
    return (
      <div className="space-y-2">
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={index}
            className={clsx(
              baseStyles,
              variantStyles[variant],
              defaultHeights[variant],
              index === lines - 1 ? 'w-3/4' : 'w-full',
              className
            )}
            style={index === 0 ? style : undefined}
          />
        ))}
      </div>
    )
  }

  return (
    <div
      className={clsx(
        baseStyles,
        variantStyles[variant],
        !height && defaultHeights[variant],
        className
      )}
      style={style}
    />
  )
}

// Preset skeleton components for common patterns
export const SkeletonCard: React.FC<{ className?: string }> = ({ className }) => (
  <div className={clsx('p-4 space-y-3', className)}>
    <Skeleton variant="text" width="60%" />
    <Skeleton variant="text" lines={2} />
    <div className="flex gap-2 pt-2">
      <Skeleton variant="rectangular" width={80} height={32} />
      <Skeleton variant="rectangular" width={80} height={32} />
    </div>
  </div>
)

export const SkeletonList: React.FC<{ items?: number; className?: string }> = ({
  items = 3,
  className,
}) => (
  <div className={clsx('space-y-4', className)}>
    {Array.from({ length: items }).map((_, index) => (
      <div key={index} className="flex items-center gap-3">
        <Skeleton variant="circular" />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="40%" />
          <Skeleton variant="text" width="70%" />
        </div>
      </div>
    ))}
  </div>
)

export const SkeletonTable: React.FC<{ rows?: number; cols?: number; className?: string }> = ({
  rows = 5,
  cols = 4,
  className,
}) => (
  <div className={clsx('space-y-2', className)}>
    {/* Header */}
    <div className="flex gap-4 pb-2 border-b border-secondary-200">
      {Array.from({ length: cols }).map((_, index) => (
        <Skeleton key={index} variant="text" className="flex-1" />
      ))}
    </div>
    {/* Rows */}
    {Array.from({ length: rows }).map((_, rowIndex) => (
      <div key={rowIndex} className="flex gap-4 py-2">
        {Array.from({ length: cols }).map((_, colIndex) => (
          <Skeleton key={colIndex} variant="text" className="flex-1" />
        ))}
      </div>
    ))}
  </div>
)

export default Skeleton

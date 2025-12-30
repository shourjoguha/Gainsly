import React, { useEffect, useRef, useCallback } from 'react'
import { createPortal } from 'react-dom'
import { clsx } from 'clsx'
import { XMarkIcon } from '@heroicons/react/24/outline'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
  title?: string
  description?: string
  size?: 'sm' | 'md' | 'lg'
  closeOnOverlayClick?: boolean
  showCloseButton?: boolean
  children: React.ReactNode
  footer?: React.ReactNode
}

const sizeStyles: Record<string, string> = {
  sm: 'max-w-sm',
  md: 'max-w-md',
  lg: 'max-w-2xl',
}

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  size = 'md',
  closeOnOverlayClick = true,
  showCloseButton = true,
  children,
  footer,
}) => {
  const overlayRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)

  // Handle escape key
  const handleEscape = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose()
      }
    },
    [onClose]
  )

  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      document.body.style.overflow = 'hidden'

      // Focus trap: focus the modal when opened
      contentRef.current?.focus()
    }

    return () => {
      document.removeEventListener('keydown', handleEscape)
      document.body.style.overflow = 'unset'
    }
  }, [isOpen, handleEscape])

  // Handle overlay click
  const handleOverlayClick = (e: React.MouseEvent) => {
    if (closeOnOverlayClick && e.target === overlayRef.current) {
      onClose()
    }
  }

  if (!isOpen) return null

  return createPortal(
    <div
      ref={overlayRef}
      className={clsx(
        'fixed inset-0 z-50',
        'flex items-center justify-center',
        'bg-black/40',
        'animate-fade-in'
      )}
      onClick={handleOverlayClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
      aria-describedby={description ? 'modal-description' : undefined}
    >
      <div
        ref={contentRef}
        tabIndex={-1}
        className={clsx(
          'relative w-full mx-4 sm:mx-0',
          sizeStyles[size],
          'bg-white rounded-modal shadow-modal',
          'p-6 sm:p-6',
          'animate-slide-up',
          'focus:outline-none'
        )}
      >
        {/* Close button */}
        {showCloseButton && (
          <button
            onClick={onClose}
            className={clsx(
              'absolute top-4 right-4',
              'w-8 h-8 flex items-center justify-center',
              'rounded-full',
              'text-secondary-400 hover:text-secondary-600 hover:bg-secondary-100',
              'transition-colors duration-fast',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary-500'
            )}
            aria-label="Close modal"
          >
            <XMarkIcon className="w-5 h-5" />
          </button>
        )}

        {/* Header */}
        {(title || description) && (
          <div className="mb-4 pr-8">
            {title && (
              <h2
                id="modal-title"
                className="text-xl font-bold text-secondary-900"
              >
                {title}
              </h2>
            )}
            {description && (
              <p
                id="modal-description"
                className="mt-1 text-sm text-secondary-600"
              >
                {description}
              </p>
            )}
          </div>
        )}

        {/* Content */}
        <div className="max-h-[60vh] overflow-y-auto">{children}</div>

        {/* Footer */}
        {footer && (
          <div className="mt-6 pt-4 border-t border-secondary-200 flex items-center justify-end gap-2">
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body
  )
}

export default Modal

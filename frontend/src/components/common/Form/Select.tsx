import React, { forwardRef } from 'react'
import { clsx } from 'clsx'
import { ChevronDownIcon } from '@heroicons/react/24/outline'

interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'children'> {
  label?: string
  error?: string
  helpText?: string
  options: SelectOption[]
  placeholder?: string
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ label, error, helpText, options, placeholder, className, id, required, ...props }, ref) => {
    const selectId = id || label?.toLowerCase().replace(/\s+/g, '-')

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={selectId}
            className="block mb-1.5 text-xs font-medium text-secondary-700"
          >
            {label}
            {required && <span className="text-destructive-500 ml-0.5">*</span>}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            id={selectId}
            className={clsx(
              'w-full h-10 pl-3 pr-10 py-2.5',
              'text-base text-secondary-900',
              'bg-white border rounded-input',
              'appearance-none cursor-pointer',
              'transition-all duration-fast',
              'focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500',
              error
                ? 'border-destructive-500 focus:border-destructive-500 focus:ring-destructive-500/20'
                : 'border-secondary-300',
              props.disabled && 'bg-secondary-100 text-secondary-500 cursor-not-allowed',
              className
            )}
            aria-invalid={error ? 'true' : undefined}
            aria-describedby={error ? `${selectId}-error` : helpText ? `${selectId}-help` : undefined}
            required={required}
            {...props}
          >
            {placeholder && (
              <option value="" disabled>
                {placeholder}
              </option>
            )}
            {options.map((option) => (
              <option key={option.value} value={option.value} disabled={option.disabled}>
                {option.label}
              </option>
            ))}
          </select>
          <ChevronDownIcon className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-secondary-400 pointer-events-none" />
        </div>
        {error && (
          <p
            id={`${selectId}-error`}
            className="mt-1 text-xs text-destructive-600 animate-fade-in flex items-center gap-1"
          >
            <svg className="w-3 h-3" viewBox="0 0 12 12" fill="currentColor">
              <path d="M6 0C2.7 0 0 2.7 0 6s2.7 6 6 6 6-2.7 6-6S9.3 0 6 0zm0 9a.75.75 0 110-1.5.75.75 0 010 1.5zm.75-3a.75.75 0 01-1.5 0V3.75a.75.75 0 011.5 0V6z" />
            </svg>
            {error}
          </p>
        )}
        {helpText && !error && (
          <p id={`${selectId}-help`} className="mt-1 text-xs text-secondary-600">
            {helpText}
          </p>
        )}
      </div>
    )
  }
)

Select.displayName = 'Select'

export default Select

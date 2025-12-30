import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Button from '../../src/components/common/Button'

describe('Button', () => {
  it('renders children text', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument()
  })

  it('calls onClick when clicked', () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>Click me</Button>)
    fireEvent.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('is disabled when disabled prop is true', () => {
    render(<Button disabled>Click me</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('is disabled when loading is true', () => {
    render(<Button loading>Click me</Button>)
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('shows spinner when loading', () => {
    render(<Button loading>Click me</Button>)
    expect(screen.getByRole('status')).toBeInTheDocument()
  })

  it('applies primary variant styles by default', () => {
    render(<Button>Click me</Button>)
    const button = screen.getByRole('button')
    expect(button).toHaveClass('bg-primary-500')
  })

  it('applies secondary variant styles', () => {
    render(<Button variant="secondary">Click me</Button>)
    const button = screen.getByRole('button')
    expect(button).toHaveClass('border-2')
  })

  it('applies danger variant styles', () => {
    render(<Button variant="danger">Click me</Button>)
    const button = screen.getByRole('button')
    expect(button).toHaveClass('bg-destructive-500')
  })

  it('applies ghost variant styles', () => {
    render(<Button variant="ghost">Click me</Button>)
    const button = screen.getByRole('button')
    expect(button).toHaveClass('text-primary-600')
  })

  it('applies full width when fullWidth is true', () => {
    render(<Button fullWidth>Click me</Button>)
    expect(screen.getByRole('button')).toHaveClass('w-full')
  })

  it('renders left icon', () => {
    render(<Button leftIcon={<span data-testid="left-icon">★</span>}>Click me</Button>)
    expect(screen.getByTestId('left-icon')).toBeInTheDocument()
  })

  it('renders right icon', () => {
    render(<Button rightIcon={<span data-testid="right-icon">★</span>}>Click me</Button>)
    expect(screen.getByTestId('right-icon')).toBeInTheDocument()
  })

  it('applies different sizes', () => {
    const { rerender } = render(<Button size="sm">Small</Button>)
    expect(screen.getByRole('button')).toHaveClass('h-8')

    rerender(<Button size="md">Medium</Button>)
    expect(screen.getByRole('button')).toHaveClass('h-10')

    rerender(<Button size="lg">Large</Button>)
    expect(screen.getByRole('button')).toHaveClass('h-12')
  })
})

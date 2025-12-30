import { useState, useEffect } from 'react'
import { BREAKPOINTS } from '../utils/constants'

/**
 * Custom hook for matching media queries
 * @param query - CSS media query string
 */
function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined') {
      return false
    }
    return window.matchMedia(query).matches
  })

  useEffect(() => {
    if (typeof window === 'undefined') {
      return
    }

    const mediaQuery = window.matchMedia(query)
    const handler = (event: MediaQueryListEvent) => setMatches(event.matches)

    // Set initial value
    setMatches(mediaQuery.matches)

    // Add listener
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [query])

  return matches
}

// Convenience hooks for common breakpoints
export function useIsMobile(): boolean {
  return !useMediaQuery(`(min-width: ${BREAKPOINTS.sm}px)`)
}

export function useIsTablet(): boolean {
  const isAboveMobile = useMediaQuery(`(min-width: ${BREAKPOINTS.sm}px)`)
  const isBelowDesktop = !useMediaQuery(`(min-width: ${BREAKPOINTS.lg}px)`)
  return isAboveMobile && isBelowDesktop
}

export function useIsDesktop(): boolean {
  return useMediaQuery(`(min-width: ${BREAKPOINTS.lg}px)`)
}

export function useBreakpoint(): 'mobile' | 'tablet' | 'desktop' {
  const isMobile = useIsMobile()
  const isDesktop = useIsDesktop()

  if (isMobile) return 'mobile'
  if (isDesktop) return 'desktop'
  return 'tablet'
}

export default useMediaQuery

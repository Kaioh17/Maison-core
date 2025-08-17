import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react'

export type Theme = 'dark' | 'light' | 'auto'

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  isDark: boolean
  isLight: boolean
  restoreTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

interface ThemeProviderProps {
  children: ReactNode
  initialTheme?: Theme
}

// Helper function to get initial theme from localStorage or system preference
function getInitialTheme(): Theme {
  try {
    // Check if we're in a browser environment
    if (typeof window === 'undefined') {
      console.log('Theme: SSR environment, defaulting to dark')
      return 'dark' // Default for SSR
    }
    
    // Check localStorage first
    const savedTheme = localStorage.getItem('theme') as Theme
    console.log('Theme: localStorage theme:', savedTheme)
    
    if (savedTheme && ['dark', 'light', 'auto'].includes(savedTheme)) {
      console.log('Theme: Using saved theme from localStorage:', savedTheme)
      return savedTheme
    }
    
    // If no saved theme, check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      console.log('Theme: No saved theme, using system preference: dark')
      return 'dark'
    }
    
    // Default to dark if no system preference detected
    console.log('Theme: No saved theme or system preference, defaulting to dark')
    return 'dark'
  } catch (error) {
    console.warn('Theme: Error getting initial theme:', error)
    return 'dark' // Fallback to dark theme
  }
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  // Initialize theme state with the value from localStorage or system preference
  const [theme, setTheme] = useState<Theme>(getInitialTheme)
  const [isDark, setIsDark] = useState<boolean>(getInitialTheme() === 'dark')
  const [isLight, setIsLight] = useState<boolean>(getInitialTheme() === 'light')
  const [isInitialized, setIsInitialized] = useState<boolean>(false)

  console.log('Theme: ThemeProvider initialized with theme:', theme)

  // Ensure theme is properly applied on mount
  useEffect(() => {
    console.log('Theme: Ensuring theme is applied on mount')
    try {
      const root = document.documentElement
      const body = document.body
      
      // Check if theme is already set correctly
      const currentRootTheme = root.getAttribute('data-theme')
      const currentBodyTheme = body.getAttribute('data-theme')
      
      console.log('Theme: Current document themes - Root:', currentRootTheme, 'Body:', currentBodyTheme, 'Expected:', theme)
      
      // Only update if different
      if (currentRootTheme !== theme) {
        root.setAttribute('data-theme', theme)
        console.log('Theme: Updated root data-theme to:', theme)
      }
      
      if (currentBodyTheme !== theme) {
        body.setAttribute('data-theme', theme)
        console.log('Theme: Updated body data-theme to:', theme)
      }
      
      console.log('Theme: Theme applied on mount:', theme)
    } catch (error) {
      console.warn('Theme: Error applying theme on mount:', error)
    }
  }, []) // Empty dependency array - only run once on mount

  // Monitor theme changes and restore if overridden
  useEffect(() => {
    const checkThemeConsistency = () => {
      try {
        const root = document.documentElement
        const body = document.body
        const currentRootTheme = root.getAttribute('data-theme')
        const currentBodyTheme = body.getAttribute('data-theme')
        
        // If theme attributes don't match our state, restore them
        if (currentRootTheme !== theme || currentBodyTheme !== theme) {
          console.log('Theme: Theme attributes inconsistent, restoring. Root:', currentRootTheme, 'Body:', currentBodyTheme, 'Expected:', theme)
          root.setAttribute('data-theme', theme)
          body.setAttribute('data-theme', theme)
        }
      } catch (error) {
        console.warn('Theme: Error checking theme consistency:', error)
      }
    }
    
    // Check every 1 second for more responsive theme restoration
    const interval = setInterval(checkThemeConsistency, 1000)
    
    // Also check when the page becomes visible (user returns to tab)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        checkThemeConsistency()
      }
    }
    
    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    return () => {
      clearInterval(interval)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [theme])

  // Apply theme to document body
  useEffect(() => {
    console.log('Theme: Applying theme:', theme)
    try {
      const root = document.documentElement
      const body = document.body
      
      // Only remove and reapply if the theme actually changed
      const currentRootTheme = root.getAttribute('data-theme')
      const currentBodyTheme = body.getAttribute('data-theme')
      
      if (currentRootTheme !== theme || currentBodyTheme !== theme) {
        console.log('Theme: Theme changed, updating attributes. Old root:', currentRootTheme, 'Old body:', currentBodyTheme, 'New:', theme)
        
        // Remove existing theme attributes
        root.removeAttribute('data-theme')
        body.removeAttribute('data-theme')
        
        // Apply new theme
        if (theme === 'auto') {
          // Auto theme - check system preference
          const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
          const isSystemDark = mediaQuery.matches
          
          console.log('Theme: Auto theme, system preference is:', isSystemDark ? 'dark' : 'light')
          
          root.setAttribute('data-theme', 'auto')
          body.setAttribute('data-theme', 'auto')
          setIsDark(isSystemDark)
          setIsLight(!isSystemDark)
          
          // Listen for system theme changes
          const handleChange = (e: MediaQueryListEvent) => {
            console.log('Theme: System theme changed to:', e.matches ? 'dark' : 'light')
            setIsDark(e.matches)
            setIsLight(!e.matches)
          }
          
          mediaQuery.addEventListener('change', handleChange)
          return () => mediaQuery.removeEventListener('change', handleChange)
        } else {
          // Manual theme
          console.log('Theme: Setting manual theme:', theme)
          root.setAttribute('data-theme', theme)
          body.setAttribute('data-theme', theme)
          setIsDark(theme === 'dark')
          setIsLight(theme === 'light')
        }
        
        console.log('Theme: Theme applied successfully. Root data-theme:', root.getAttribute('data-theme'), 'Body data-theme:', body.getAttribute('data-theme'))
      } else {
        console.log('Theme: Theme unchanged, no update needed')
      }
      
      setIsInitialized(true)
    } catch (error) {
      console.warn('Theme: Error applying theme:', error)
      // Fallback to dark theme
      document.documentElement.setAttribute('data-theme', 'dark')
      document.body.setAttribute('data-theme', 'dark')
      setIsDark(true)
      setIsLight(false)
      setIsInitialized(true)
    }
  }, [theme])

  // Save theme to localStorage when it changes
  useEffect(() => {
    if (isInitialized) { // Only save after initial theme is applied
      try {
        if (typeof window !== 'undefined') {
          console.log('Theme: Saving theme to localStorage:', theme)
          localStorage.setItem('theme', theme)
          
          // Also update the document attribute immediately for better persistence
          document.documentElement.setAttribute('data-theme', theme)
          document.body.setAttribute('data-theme', theme)
          
          console.log('Theme: Theme saved to localStorage and document attributes successfully')
        }
      } catch (error) {
        console.warn('Theme: Error saving theme to localStorage:', error)
      }
    }
  }, [theme, isInitialized])

  const restoreTheme = () => {
    try {
      const root = document.documentElement
      const body = document.body
      root.setAttribute('data-theme', theme)
      body.setAttribute('data-theme', theme)
      console.log('Theme: Theme restored to:', theme)
    } catch (error) {
      console.warn('Theme: Error restoring theme:', error)
    }
  }

  const value: ThemeContextType = {
    theme,
    setTheme,
    isDark,
    isLight,
    restoreTheme
  }

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}

// Hook to sync theme with tenant settings
export function useTenantTheme(tenantTheme?: string) {
  const { theme, setTheme } = useTheme()
  
  useEffect(() => {
    // Only override user's theme if they haven't explicitly set one
    // or if they're using auto mode and tenant has a specific theme
    if (tenantTheme && ['dark', 'light', 'auto'].includes(tenantTheme)) {
      try {
        const savedTheme = localStorage.getItem('theme') as Theme
        
        // If user has explicitly set a theme (not auto), don't override it
        if (savedTheme && savedTheme !== 'auto') {
          console.log('Theme: User has explicit theme preference:', savedTheme, 'not overriding with tenant theme:', tenantTheme)
          return
        }
        
        // Only set tenant theme if user is using auto mode or no preference
        if (theme === 'auto' || !savedTheme) {
          console.log('Theme: Syncing with tenant theme:', tenantTheme)
          setTheme(tenantTheme as Theme)
        }
      } catch (error) {
        console.warn('Theme: Error checking localStorage for theme preference:', error)
      }
    }
  }, [tenantTheme, setTheme, theme])
} 
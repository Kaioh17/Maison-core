import React from 'react'
import { Moon, Sun, Monitor } from 'lucide-react'
import { useTheme } from '@contexts/ThemeContext'

export default function ThemeToggle() {
  const { theme, setTheme, isDark, isLight, restoreTheme } = useTheme()

  const handleThemeChange = (newTheme: 'dark' | 'light' | 'auto') => {
    setTheme(newTheme)
  }

  const handleThemeRestore = () => {
    restoreTheme()
  }

  const getThemeIcon = () => {
    switch (theme) {
      case 'light':
        return <Sun className="w-4 h-4" />
      case 'dark':
        return <Moon className="w-4 h-4" />
      case 'auto':
        return <Monitor className="w-4 h-4" />
      default:
        return <Monitor className="w-4 h-4" />
    }
  }

  const getThemeLabel = () => {
    switch (theme) {
      case 'light':
        return 'Light Mode'
      case 'dark':
        return 'Dark Mode'
      case 'auto':
        return 'Auto (System)'
      default:
        return 'Auto (System)'
    }
  }

  return (
    <div className="theme-toggle">
      <div className="theme-toggle-current" style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px',
        padding: '8px 12px',
        borderRadius: '6px',
        background: 'var(--bw-bg-hover)',
        border: '1px solid var(--bw-border)',
        cursor: 'pointer',
        transition: 'all 0.2s ease'
      }}
      onClick={() => {
        // Cycle through themes: dark -> light -> auto -> dark
        if (theme === 'dark') handleThemeChange('light')
        else if (theme === 'light') handleThemeChange('auto')
        else handleThemeChange('dark')
      }}
      onContextMenu={(e) => {
        e.preventDefault()
        handleThemeRestore()
      }}
      title="Right-click to restore theme if it gets overridden"
      onMouseEnter={(e) => {
        e.currentTarget.style.background = 'var(--bw-bg-hover-strong)'
        e.currentTarget.style.borderColor = 'var(--bw-accent)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.background = 'var(--bw-bg-hover)'
        e.currentTarget.style.borderColor = 'var(--bw-border)'
      }}
      >
        {getThemeIcon()}
        <span style={{ 
          fontSize: '14px', 
          fontWeight: '500',
          color: 'var(--bw-fg)'
        }}>
          {getThemeLabel()}
        </span>
      </div>
      
      <div className="theme-toggle-dropdown" style={{
        position: 'absolute',
        top: '100%',
        right: '0',
        marginTop: '4px',
        background: 'var(--bw-bg)',
        border: '1px solid var(--bw-border)',
        borderRadius: '8px',
        boxShadow: 'var(--bw-shadow)',
        padding: '8px 0',
        minWidth: '160px',
        zIndex: 1000,
        display: 'none'
      }}>
        <div className="theme-option" style={{
          padding: '8px 16px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          transition: 'background 0.2s ease'
        }}
        onClick={() => handleThemeChange('light')}
        onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bw-bg-hover)'}
        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
          <Sun className="w-4 h-4" />
          <span>Light Mode</span>
        </div>
        
        <div className="theme-option" style={{
          padding: '8px 16px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          transition: 'background 0.2s ease'
        }}
        onClick={() => handleThemeChange('dark')}
        onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bw-bg-hover)'}
        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
          <Moon className="w-4 h-4" />
          <span>Dark Mode</span>
        </div>
        
        <div className="theme-option" style={{
          padding: '8px 16px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          transition: 'background 0.2s ease'
        }}
        onClick={() => handleThemeChange('auto')}
        onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bw-bg-hover)'}
        onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
          <Monitor className="w-4 h-4" />
          <span>Auto (System)</span>
        </div>
      </div>
    </div>
  )
} 
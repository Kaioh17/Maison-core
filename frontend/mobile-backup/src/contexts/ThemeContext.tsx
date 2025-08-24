import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useColorScheme } from 'react-native';

export type Theme = 'dark' | 'light' | 'auto';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  isDark: boolean;
  isLight: boolean;
  colors: ThemeColors;
}

interface ThemeColors {
  primary: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  accent: string;
  error: string;
  success: string;
  warning: string;
}

const darkColors: ThemeColors = {
  primary: '#3b82f6',
  background: '#000000',
  surface: '#1a1a1a',
  text: '#ffffff',
  textSecondary: '#9ca3af',
  border: '#374151',
  accent: '#3b82f6',
  error: '#ef4444',
  success: '#10b981',
  warning: '#f59e0b',
};

const lightColors: ThemeColors = {
  primary: '#3b82f6',
  background: '#ffffff',
  surface: '#f9fafb',
  text: '#1f2937',
  textSecondary: '#6b7280',
  border: '#e5e7eb',
  accent: '#3b82f6',
  error: '#ef4444',
  success: '#10b981',
  warning: '#f59e0b',
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const systemColorScheme = useColorScheme();
  const [theme, setTheme] = useState<Theme>('auto');
  const [isDark, setIsDark] = useState<boolean>(true);
  const [isLight, setIsLight] = useState<boolean>(false);

  useEffect(() => {
    loadStoredTheme();
  }, []);

  useEffect(() => {
    updateThemeState();
  }, [theme, systemColorScheme]);

  const loadStoredTheme = async () => {
    try {
      const storedTheme = await AsyncStorage.getItem('theme');
      if (storedTheme && ['dark', 'light', 'auto'].includes(storedTheme)) {
        setTheme(storedTheme as Theme);
      }
    } catch (error) {
      console.error('Error loading stored theme:', error);
    }
  };

  const updateThemeState = () => {
    let effectiveTheme: 'dark' | 'light';
    
    if (theme === 'auto') {
      effectiveTheme = systemColorScheme || 'dark';
    } else {
      effectiveTheme = theme;
    }

    setIsDark(effectiveTheme === 'dark');
    setIsLight(effectiveTheme === 'light');
  };

  const handleSetTheme = async (newTheme: Theme) => {
    try {
      setTheme(newTheme);
      await AsyncStorage.setItem('theme', newTheme);
    } catch (error) {
      console.error('Error saving theme:', error);
    }
  };

  const colors = isDark ? darkColors : lightColors;

  const value: ThemeContextType = {
    theme,
    setTheme: handleSetTheme,
    isDark,
    isLight,
    colors,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
} 
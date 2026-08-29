import { useState, useEffect } from 'react'

export function useTheme() {
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem('crossword-theme') || 'system'
    } catch {
      return 'system'
    }
  })

  useEffect(() => {
    if (theme === 'system') {
      document.documentElement.removeAttribute('data-theme')
    } else {
      document.documentElement.setAttribute('data-theme', theme)
    }
    try {
      localStorage.setItem('crossword-theme', theme)
    } catch {}
  }, [theme])

  const toggleTheme = () => {
    setTheme(prev => {
      if (prev === 'system') {
        const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        return isDark ? 'light' : 'dark'
      }
      return prev === 'dark' ? 'light' : 'dark'
    })
  }

  const isDark = theme === 'dark' ||
    (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)

  return { theme, isDark, toggleTheme }
}

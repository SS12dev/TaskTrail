/**
 * TaskTrail Design System
 * Modern, sophisticated color palette and design tokens
 */

export const designSystem = {
  // Color Palette - Inspired by Linear, Notion, and modern productivity apps
  colors: {
    // Primary - Vibrant Purple/Indigo for main actions
    primary: {
      50: '#f5f3ff',
      100: '#ede9fe',
      200: '#ddd6fe',
      300: '#c4b5fd',
      400: '#a78bfa',
      500: '#8b5cf6',  // Main brand color
      600: '#7c3aed',
      700: '#6d28d9',
      800: '#5b21b6',
      900: '#4c1d95',
    },

    // Accent - Cyan/Teal for highlights and interactive elements
    accent: {
      50: '#ecfeff',
      100: '#cffafe',
      200: '#a5f3fc',
      300: '#67e8f9',
      400: '#22d3ee',
      500: '#06b6d4',  // Main accent
      600: '#0891b2',
      700: '#0e7490',
      800: '#155e75',
      900: '#164e63',
    },

    // Success - Emerald green
    success: {
      50: '#ecfdf5',
      100: '#d1fae5',
      500: '#10b981',
      600: '#059669',
      700: '#047857',
    },

    // Warning - Amber
    warning: {
      50: '#fffbeb',
      100: '#fef3c7',
      500: '#f59e0b',
      600: '#d97706',
      700: '#b45309',
    },

    // Danger - Rose/Red
    danger: {
      50: '#fef2f2',
      100: '#fee2e2',
      500: '#ef4444',
      600: '#dc2626',
      700: '#b91c1c',
    },

    // Neutral - Cool gray with slight blue tint
    neutral: {
      50: '#f8fafc',
      100: '#f1f5f9',
      200: '#e2e8f0',
      300: '#cbd5e1',
      400: '#94a3b8',
      500: '#64748b',
      600: '#475569',
      700: '#334155',
      800: '#1e293b',
      900: '#0f172a',
    },
  },

  // Status Colors - For task status indicators
  status: {
    todo: {
      bg: '#ddd6fe',      // primary-200
      text: '#6d28d9',    // primary-700
      border: '#c4b5fd',  // primary-300
    },
    inProgress: {
      bg: '#a5f3fc',      // accent-200
      text: '#0e7490',    // accent-700
      border: '#67e8f9',  // accent-300
    },
    done: {
      bg: '#d1fae5',      // success-100
      text: '#047857',    // success-700
      border: '#10b981',  // success-500
    },
  },

  // Priority Colors
  priority: {
    urgent: {
      bg: '#fee2e2',      // danger-100
      text: '#b91c1c',    // danger-700
      icon: '#ef4444',    // danger-500
    },
    high: {
      bg: '#fef3c7',      // warning-100
      text: '#b45309',    // warning-700
      icon: '#f59e0b',    // warning-500
    },
    medium: {
      bg: '#a5f3fc',      // accent-200
      text: '#0e7490',    // accent-700
      icon: '#06b6d4',    // accent-500
    },
    low: {
      bg: '#f1f5f9',      // neutral-100
      text: '#475569',    // neutral-600
      icon: '#94a3b8',    // neutral-400
    },
  },

  // Gradients
  gradients: {
    primary: 'linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%)',
    accent: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
    success: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    sunset: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)',
    ocean: 'linear-gradient(135deg, #06b6d4 0%, #8b5cf6 100%)',
    twilight: 'linear-gradient(135deg, #6d28d9 0%, #1e293b 100%)',
  },

  // Shadows - Layered depth system
  shadows: {
    sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
    md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
    lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
    xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
    inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',

    // Colored shadows for emphasis
    primaryGlow: '0 8px 16px -4px rgba(139, 92, 246, 0.3)',
    accentGlow: '0 8px 16px -4px rgba(6, 182, 212, 0.3)',
    successGlow: '0 8px 16px -4px rgba(16, 185, 129, 0.3)',
  },

  // Border Radius
  radius: {
    sm: '0.375rem',   // 6px
    md: '0.5rem',     // 8px
    lg: '0.75rem',    // 12px
    xl: '1rem',       // 16px
    '2xl': '1.5rem',  // 24px
    full: '9999px',
  },

  // Spacing scale (matches Tailwind)
  spacing: {
    xs: '0.5rem',   // 8px
    sm: '0.75rem',  // 12px
    md: '1rem',     // 16px
    lg: '1.5rem',   // 24px
    xl: '2rem',     // 32px
    '2xl': '3rem',  // 48px
  },

  // Typography
  typography: {
    fontFamily: {
      sans: 'Inter, system-ui, -apple-system, sans-serif',
      mono: 'JetBrains Mono, monospace',
    },
    fontSize: {
      xs: '0.75rem',    // 12px
      sm: '0.875rem',   // 14px
      base: '1rem',     // 16px
      lg: '1.125rem',   // 18px
      xl: '1.25rem',    // 20px
      '2xl': '1.5rem',  // 24px
      '3xl': '1.875rem', // 30px
      '4xl': '2.25rem', // 36px
    },
    fontWeight: {
      normal: '400',
      medium: '500',
      semibold: '600',
      bold: '700',
    },
  },

  // Transitions
  transitions: {
    fast: '150ms cubic-bezier(0.4, 0, 0.2, 1)',
    base: '200ms cubic-bezier(0.4, 0, 0.2, 1)',
    slow: '300ms cubic-bezier(0.4, 0, 0.2, 1)',
    spring: '500ms cubic-bezier(0.34, 1.56, 0.64, 1)',
  },

  // Z-Index layers
  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modalBackdrop: 1040,
    modal: 1050,
    popover: 1060,
    tooltip: 1070,
  },
} as const;

export type DesignSystem = typeof designSystem;

// Design System Constants for Nuetra Platform
// Based on brand identity and modern UI best practices

export const COLORS = {
  // Brand Colors (from Nuetra logo and landing page)
  primary: {
    main: '#64ae00',      // Nuetra green
    light: '#7dc41f',     // Lighter shade
    dark: '#4d8500',      // Darker shade
    50: 'rgba(100, 174, 0, 0.05)',
    100: 'rgba(100, 174, 0, 0.1)',
    200: 'rgba(100, 174, 0, 0.2)',
    300: 'rgba(100, 174, 0, 0.3)',
    500: 'rgba(100, 174, 0, 0.5)',
    600: 'rgba(100, 174, 0, 0.6)',
    800: 'rgba(100, 174, 0, 0.8)',
    900: 'rgba(100, 174, 0, 0.9)',
  },
  secondary: {
    main: '#404040',      // Dark gray
    light: '#5a5a5a',
    dark: '#2a2a2a',
  },
  tertiary: {
    main: '#f3f6ea',      // Light cream
    light: '#f8faf4',
    dark: '#e8eedc',
  },
  
  // Neutral palette
  neutral: {
    white: '#ffffff',
    50: '#fafafa',
    100: '#f5f5f5',
    200: '#eeeeee',
    300: '#e0e0e0',
    400: '#bdbdbd',
    500: '#9e9e9e',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
  },
  
  // Semantic colors
  success: {
    main: '#10b981',
    light: '#34d399',
    dark: '#059669',
    bg: '#ecfdf5',
  },
  error: {
    main: '#ef4444',
    light: '#f87171',
    dark: '#dc2626',
    bg: '#fef2f2',
  },
  warning: {
    main: '#f59e0b',
    light: '#fbbf24',
    dark: '#d97706',
    bg: '#fffbeb',
  },
  info: {
    main: '#3b82f6',
    light: '#60a5fa',
    dark: '#2563eb',
    bg: '#eff6ff',
  },
  
  // Wellness category colors (matching design references)
  wellness: {
    mindfulness: {
      gradient: 'from-purple-500 to-purple-600',
      solid: '#a855f7',
      bg: '#faf5ff',
    },
    physical: {
      gradient: 'from-green-500 to-green-600',
      solid: '#22c55e',
      bg: '#f0fdf4',
    },
    mental: {
      gradient: 'from-pink-500 to-rose-600',
      solid: '#ec4899',
      bg: '#fdf2f8',
    },
    nutrition: {
      gradient: 'from-orange-500 to-orange-600',
      solid: '#f97316',
      bg: '#fff7ed',
    },
    stress: {
      gradient: 'from-blue-500 to-indigo-600',
      solid: '#3b82f6',
      bg: '#eff6ff',
    },
  },
};

export const TYPOGRAPHY = {
  fontFamily: {
    sans: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    mono: '"SF Mono", Monaco, "Cascadia Code", "Roboto Mono", monospace',
  },
  fontSize: {
    xs: '0.75rem',      // 12px
    sm: '0.875rem',     // 14px
    base: '1rem',       // 16px
    lg: '1.125rem',     // 18px
    xl: '1.25rem',      // 20px
    '2xl': '1.5rem',    // 24px
    '3xl': '1.875rem',  // 30px
    '4xl': '2.25rem',   // 36px
    '5xl': '3rem',      // 48px
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
};

export const SPACING = {
  0: '0',
  1: '0.25rem',   // 4px
  2: '0.5rem',    // 8px
  3: '0.75rem',   // 12px
  4: '1rem',      // 16px
  5: '1.25rem',   // 20px
  6: '1.5rem',    // 24px
  7: '1.75rem',   // 28px
  8: '2rem',      // 32px
  10: '2.5rem',   // 40px
  12: '3rem',     // 48px
  16: '4rem',     // 64px
  20: '5rem',     // 80px
  24: '6rem',     // 96px
};

export const BORDER_RADIUS = {
  none: '0',
  sm: '0.375rem',   // 6px
  base: '0.5rem',   // 8px
  md: '0.75rem',    // 12px
  lg: '1rem',       // 16px
  xl: '1.25rem',    // 20px
  '2xl': '1.5rem',  // 24px
  full: '9999px',
};

export const SHADOWS = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  base: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  
  // Custom shadows with brand color
  primaryGlow: '0 0 20px rgba(100, 174, 0, 0.3)',
  primaryGlowLg: '0 0 40px rgba(100, 174, 0, 0.4)',
  
  // Card shadows
  card: '0 1px 3px rgba(0, 0, 0, 0.05), 0 1px 2px rgba(0, 0, 0, 0.03)',
  cardHover: '0 8px 16px rgba(0, 0, 0, 0.1), 0 3px 6px rgba(0, 0, 0, 0.05)',
};

export const TRANSITIONS = {
  fast: '150ms ease-in-out',
  base: '200ms ease-in-out',
  slow: '300ms ease-in-out',
  slower: '500ms ease-in-out',
};

export const BREAKPOINTS = {
  xs: '320px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
};

export const Z_INDEX = {
  dropdown: 1000,
  sticky: 1020,
  fixed: 1030,
  modalBackdrop: 1040,
  modal: 1050,
  popover: 1060,
  tooltip: 1070,
};

// Glassmorphism effect settings
export const GLASS_EFFECT = {
  light: {
    background: 'rgba(255, 255, 255, 0.7)',
    backdropBlur: 'blur(10px)',
    border: '1px solid rgba(255, 255, 255, 0.3)',
  },
  dark: {
    background: 'rgba(0, 0, 0, 0.3)',
    backdropBlur: 'blur(10px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  primary: {
    background: 'rgba(100, 174, 0, 0.1)',
    backdropBlur: 'blur(10px)',
    border: '1px solid rgba(100, 174, 0, 0.2)',
  },
};

// Animation durations
export const ANIMATION = {
  duration: {
    fast: 200,
    normal: 300,
    slow: 500,
  },
  easing: {
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    spring: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  },
};

// Grid and layout constants
export const LAYOUT = {
  containerMaxWidth: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
  sidebarWidth: '280px',
  sidebarCollapsedWidth: '80px',
  headerHeight: '72px',
  mobileHeaderHeight: '64px',
};

// Icon sizes
export const ICON_SIZES = {
  xs: 12,
  sm: 16,
  base: 20,
  lg: 24,
  xl: 32,
  '2xl': 40,
};

// Button sizes
export const BUTTON_SIZES = {
  sm: {
    height: '32px',
    padding: '0 12px',
    fontSize: '0.875rem',
  },
  base: {
    height: '40px',
    padding: '0 16px',
    fontSize: '1rem',
  },
  lg: {
    height: '48px',
    padding: '0 24px',
    fontSize: '1.125rem',
  },
};

// Card variants
export const CARD_VARIANTS = {
  default: {
    background: COLORS.neutral.white,
    border: `1px solid ${COLORS.neutral[200]}`,
    borderRadius: BORDER_RADIUS.lg,
    shadow: SHADOWS.card,
  },
  elevated: {
    background: COLORS.neutral.white,
    border: 'none',
    borderRadius: BORDER_RADIUS.xl,
    shadow: SHADOWS.lg,
  },
  glass: {
    background: GLASS_EFFECT.light.background,
    border: GLASS_EFFECT.light.border,
    borderRadius: BORDER_RADIUS.xl,
    backdropFilter: GLASS_EFFECT.light.backdropBlur,
  },
};

export default {
  COLORS,
  TYPOGRAPHY,
  SPACING,
  BORDER_RADIUS,
  SHADOWS,
  TRANSITIONS,
  BREAKPOINTS,
  Z_INDEX,
  GLASS_EFFECT,
  ANIMATION,
  LAYOUT,
  ICON_SIZES,
  BUTTON_SIZES,
  CARD_VARIANTS,
};


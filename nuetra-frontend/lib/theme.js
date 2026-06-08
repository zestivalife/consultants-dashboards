// Theme configuration based on landing page design
// Primary color: #64ae00 (green)
// Gradients: from-green-500 to-blue-500

export const theme = {
  colors: {
    primary: '#64ae00',
    primaryDark: '#579700',
    primaryLight: '#4f9600',
    primaryHover: '#5b9e00',
    gradient: {
      from: 'from-green-500',
      to: 'to-blue-500',
      fromHex: '#10b981', // green-500
      toHex: '#3b82f6', // blue-500
    },
    background: {
      light: '#f9fafb', // gray-50
      white: '#ffffff',
      green: {
        50: '#f0fdf4',
        100: '#dcfce7',
      }
    },
    text: {
      primary: '#111827', // gray-900
      secondary: '#4b5563', // gray-600
      muted: '#6b7280', // gray-500
    },
    accent: {
      green: '#10b981', // green-500
      blue: '#3b82f6', // blue-500
      purple: '#8b5cf6', // purple-500
    },
    border: {
      default: '#e5e7eb', // gray-200
      hover: '#64ae00',
    }
  },
  spacing: {
    xs: '0.5rem',
    sm: '1rem',
    md: '1.5rem',
    lg: '2rem',
    xl: '3rem',
  },
  borderRadius: {
    sm: '0.5rem',
    md: '0.75rem',
    lg: '1rem',
    full: '9999px',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
  }
};

// Tailwind CSS classes for consistent styling
export const themeClasses = {
  button: {
    primary: 'px-6 py-2 rounded-full text-white bg-[#64ae00] hover:bg-[#579700] transition-all font-medium shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#64ae00]',
    secondary: 'px-6 py-2 border-2 border-[#64ae00] rounded-full text-[#64ae00] font-medium hover:bg-[#f3fbde] transition-all',
    outline: 'px-6 py-2 border border-gray-300 rounded-lg text-gray-700 hover:border-[#64ae00] hover:text-[#64ae00] transition-all',
  },
  card: {
    default: 'bg-white rounded-xl border border-gray-200 shadow-md hover:shadow-lg transition-shadow',
    elevated: 'bg-white rounded-xl border-2 border-gray-100 shadow-lg',
    gradient: 'bg-gradient-to-br from-green-500 to-blue-500 rounded-xl text-white',
  },
  input: {
    default: 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#64ae00] focus:border-transparent transition-all',
    error: 'w-full px-4 py-3 border border-red-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-transparent',
  },
  link: {
    default: 'text-gray-600 hover:text-[#64ae00] transition-colors font-medium',
    primary: 'text-[#64ae00] hover:text-[#579700] font-medium',
  },
  badge: {
    primary: 'px-3 py-1 bg-[#64ae00]/10 text-green-800 rounded-full font-medium',
    success: 'px-3 py-1 bg-green-100 text-green-800 rounded-full font-medium',
    warning: 'px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full font-medium',
    error: 'px-3 py-1 bg-red-100 text-red-800 rounded-full font-medium',
  }
};

export default theme;


import type { Config } from 'tailwindcss'
import forms from '@tailwindcss/forms'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Primary brand colors
        'primary': {
          50: '#f0f9fc',
          100: '#e0f2f9',
          200: '#b3e0f0',
          300: '#80cde8',
          400: '#4db8e0',
          500: '#06B6D4', // Main teal
          600: '#0891B2',
          700: '#0b7ba7',
          800: '#0d5f84',
          900: '#164e63',
        },
        // Secondary slate
        'secondary': {
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
        // Accent amber
        'accent': {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#F59E0B', // Main amber
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        // Success emerald
        'success': {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#10B981', // Main emerald
          600: '#059669',
          700: '#047857',
          800: '#065f46',
          900: '#064e3b',
        },
        // Destructive rose
        'destructive': {
          50: '#fff5f7',
          100: '#ffe4e9',
          200: '#ffc9d3',
          300: '#ffaabb',
          400: '#ff8aa0',
          500: '#F43F5E', // Main rose
          600: '#e11d48',
          700: '#be123c',
          800: '#9d174d',
          900: '#831843',
        },
      },
      fontFamily: {
        'sans': ['Inter', 'system-ui', 'sans-serif'],
        'mono': ['Fira Code', 'monospace'],
      },
      fontSize: {
        'xs': ['12px', { lineHeight: '1.5' }],
        'sm': ['14px', { lineHeight: '1.6' }],
        'base': ['16px', { lineHeight: '1.6' }],
        'lg': ['18px', { lineHeight: '1.4' }],
        'xl': ['20px', { lineHeight: '1.3' }],
        '2xl': ['24px', { lineHeight: '1.3' }],
        '3xl': ['32px', { lineHeight: '1.2' }],
      },
      spacing: {
        'xs': '4px',
        'sm': '8px',
        'md': '16px',
        'lg': '24px',
        'xl': '32px',
        '2xl': '48px',
      },
      borderRadius: {
        'btn': '8px',
        'modal': '12px',
        'card': '8px',
        'input': '6px',
      },
      boxShadow: {
        'modal': '0 20px 25px -5px rgba(0,0,0,0.1)',
        'elevation': '0 10px 15px -3px rgba(0,0,0,0.1)',
      },
      animation: {
        'fade-in': 'fadeIn 150ms ease-in-out',
        'fade-out': 'fadeOut 100ms ease-in-out',
        'slide-up': 'slideUp 150ms ease-in-out',
        'slide-down': 'slideDown 100ms ease-in-out',
        'pulse': 'pulse 2s ease-in-out infinite',
        'spin': 'spin 1s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeOut: {
          '0%': { opacity: '1' },
          '100%': { opacity: '0' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideDown: {
          '0%': { opacity: '1', transform: 'translateY(0)' },
          '100%': { opacity: '0', transform: 'translateY(-8px)' },
        },
      },
      transitionDuration: {
        'fast': '100ms',
        'base': '200ms',
        'slow': '300ms',
      },
    },
  },
  plugins: [forms],
} satisfies Config

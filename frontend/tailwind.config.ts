import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: 'rgb(var(--background) / <alpha-value>)',
        'background-subtle': 'rgb(var(--background-subtle) / <alpha-value>)',
        'background-raised': 'rgb(var(--background-raised) / <alpha-value>)',
        card: 'rgb(var(--card) / <alpha-value>)',
        foreground: 'rgb(var(--foreground) / <alpha-value>)',
        muted: 'rgb(var(--foreground-muted) / <alpha-value>)',
        subtle: 'rgb(var(--foreground-subtle) / <alpha-value>)',
        border: 'rgb(var(--border) / <alpha-value>)',
        'border-strong': 'rgb(var(--border-strong) / <alpha-value>)',
        accent: 'rgb(var(--accent) / <alpha-value>)',
        'accent-foreground': 'rgb(var(--accent-foreground) / <alpha-value>)',
        success: 'rgb(var(--success) / <alpha-value>)',
        'success-bg': 'rgb(var(--success-bg) / <alpha-value>)',
        warning: 'rgb(var(--warning) / <alpha-value>)',
        'warning-bg': 'rgb(var(--warning-bg) / <alpha-value>)',
        danger: 'rgb(var(--danger) / <alpha-value>)',
        'danger-bg': 'rgb(var(--danger-bg) / <alpha-value>)',
        neutral: 'rgb(var(--neutral) / <alpha-value>)',
        'neutral-bg': 'rgb(var(--neutral-bg) / <alpha-value>)',
      },
      fontFamily: {
        sans: ['Geist', 'DM Sans', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
} satisfies Config

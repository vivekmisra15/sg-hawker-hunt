import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        accent: '#f59e0b',
      },
      fontFamily: {
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
        mono: ['GeistMono', 'ui-monospace', 'monospace'],
      },
      backgroundColor: {
        base: '#0a0a0a',
      },
    },
  },
  plugins: [],
} satisfies Config

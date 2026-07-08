/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        severity: {
          critical: '#dc2626',
          warning: '#f59e0b',
          info: '#3b82f6',
          crowd: '#8b5cf6',
        }
      },
      animation: {
        'flash': 'flash 0.5s ease-in-out',
        'pulse-urgent': 'pulse-urgent 1s infinite',
      },
      keyframes: {
        flash: {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.3 },
        },
        'pulse-urgent': {
          '0%, 100%': { backgroundColor: '#dc2626' },
          '50%': { backgroundColor: '#ef4444' },
        }
      }
    },
  },
  plugins: [],
}
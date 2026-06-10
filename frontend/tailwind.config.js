/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: '#070910',
        'deep-space': '#05070a',
        panel: 'rgba(13, 18, 30, 0.7)',
        'panel-light': 'rgba(255, 255, 255, 0.03)',
        cyan: { DEFAULT: '#00f2ff', glow: 'rgba(0,242,255,0.35)', neon: '#00f2ff' },
        purple: { DEFAULT: '#8b5cf6', glow: 'rgba(139,92,246,0.3)', neon: '#8b5cf6' },
        emerald: { neon: '#10b981' },
      },
      animation: {
        'scan': 'scan 3s linear infinite',
        'float': 'float 6s ease-in-out infinite',
        'pulse-slow': 'pulse 4s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        scan: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100%)' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        }
      },
      fontFamily: {
        sans: ['Outfit', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}

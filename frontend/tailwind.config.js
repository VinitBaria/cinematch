/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        netflix: {
          red: "#E50914",
          redDark: "#B81D24",
          black: "#141414",
          darkGray: "#181818",
          card: "#222222",
          lightGray: "#E5E5E5",
          muted: "#808080",
        },
      },
      fontFamily: {
        sans: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-vignette': 'linear-gradient(to top, #141414 10%, rgba(20,20,20,0.7) 40%, rgba(20,20,20,0) 80%)',
        'hero-side': 'linear-gradient(to right, #141414 15%, rgba(20,20,20,0.6) 45%, rgba(20,20,20,0) 85%)',
      },
    },
  },
  plugins: [],
}

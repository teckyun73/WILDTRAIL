/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        forest: {
          50: "#f3f8f4",
          100: "#e3efe6",
          500: "#2f6b4f",
          700: "#1f4a37",
          900: "#132d22",
        },
        sand: "#f4efe6",
      },
      fontFamily: {
        display: ["Georgia", "serif"],
      },
    },
  },
  plugins: [],
};

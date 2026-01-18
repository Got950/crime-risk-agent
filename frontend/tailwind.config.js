/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        spade: {
          blue: "#1A4B84",
          navy: "#112D4E",
          sky: "#3F72AF",
          light: "#DBE2EF",
          gray: "#F7F7F7",
        },
      },
    },
  },
  plugins: [],
};


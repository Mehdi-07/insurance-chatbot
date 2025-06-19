/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  // This enables the DaisyUI plugin
  plugins: [require("daisyui")],

  // This adds your custom theme colors from your plan
  daisyui: {
    themes: [
      {
        tpi_theme: {
          "primary": "#0057B8",   // Royal Blue
          "accent": "#FFB81C",    // Gold
          "success": "#2E8B57",  // Emerald
          "error": "#C32424",    // Cranberry
          "base-100": "#ffffff", // Base background color
        },
      },
    ],
  },
}
/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-geist-sans)", "Geist", "Inter", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
        mono: ["var(--font-geist-mono)", "Geist Mono", "JetBrains Mono", "ui-monospace", "monospace"],
      },
      colors: {
        zinc: {
          850: "#1f1f23",
          900: "#18181b",
          950: "#09090b",
        },
        brand: {
          50: "#f4f4f5",
          100: "#e4e4e7",
          500: "#71717a",
          600: "#52525b",
          700: "#3f3f46",
          900: "#18181b",
        },
      },
    },
  },
  plugins: [],
};


import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        canvas: "#fbfaf6",
        ink: {
          DEFAULT: "#1d1d1a",
          muted: "#6b6960",
          subtle: "#9b988e",
        },
        line: "#e8e5dc",
        magnus: {
          50:  "#f1f6f1",
          100: "#dde9dd",
          200: "#bbd1bb",
          300: "#94b598",
          400: "#6e9676",
          500: "#4f7a59",
          600: "#3d6347",
          700: "#314f39",
          800: "#28402f",
          900: "#1f3024",
        },
      },
      boxShadow: {
        card: "0 1px 2px rgba(20, 24, 19, 0.04), 0 4px 16px rgba(20, 24, 19, 0.04)",
        "card-hover":
          "0 1px 2px rgba(20, 24, 19, 0.06), 0 8px 28px rgba(20, 24, 19, 0.08)",
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.125rem",
      },
    },
  },
  plugins: [],
};

export default config;

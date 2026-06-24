/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: "#0b0f17", soft: "#111827", panel: "#161d2b" },
        line: "#243042",
        accent: { DEFAULT: "#6ea8fe", dim: "#3b5bdb" },
        rag: { red: "#ef4444", amber: "#f59e0b", green: "#22c55e" },
      },
    },
  },
  plugins: [],
};

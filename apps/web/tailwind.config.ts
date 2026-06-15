import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}", "./lib/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#17212b",
        muted: "#667085",
        panel: "#f8fafc",
        line: "#d9e2ec",
        teal: "#0f766e",
        coral: "#d95f43",
        gold: "#b7791f"
      },
      boxShadow: {
        soft: "0 16px 45px rgba(23, 33, 43, 0.08)"
      }
    }
  },
  plugins: []
};

export default config;


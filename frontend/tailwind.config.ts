import type { Config } from "tailwindcss";

/**
 * Токены дизайн-системы. Меняются здесь и нигде больше:
 * в компонентах не должно остаться ни одного шестнадцатеричного цвета.
 */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#0A0B0D",
        sheet: "#101317",
        line: "#242830",
        "line-soft": "#181B20",
        bone: "#EDE7DA",
        muted: "#7B8290",
        dim: "#434A54",
        signal: "#6FE3D2",
        brass: "#D9A441",
        danger: "#E0614D",
      },
      fontFamily: {
        // Заголовки и задача дня. Геометричный, техничный, с кириллицей.
        display: ["Jura", "system-ui", "sans-serif"],
        // Текст. Родной для iOS и Android — ничего не грузим.
        sans: ["-apple-system", "Segoe UI", "Roboto", "system-ui", "sans-serif"],
        // Все числа и метки капсом.
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
      letterSpacing: {
        // Свои значения, а не переопределение встроенных: tracking-wide
        // из Tailwind должен остаться самим собой.
        label: "0.19em",
        meta: "0.16em",
      },
      borderRadius: { sheet: "22px" },
    },
  },
  plugins: [],
} satisfies Config;

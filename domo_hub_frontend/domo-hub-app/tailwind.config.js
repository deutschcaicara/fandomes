/** @type {import('tailwindcss').Config} */
import colors from 'tailwindcss/colors.js'          // acesso à paleta v3

export default {
  /* Caminhos que contêm classes Tailwind */
  content: ['./index.html', './src/**/*.{ts,tsx}'],

  /*
    REF: Tailwind v4 removeu todas as cores utilitárias.
    Aqui re‑exportamos apenas as escalas que já aparecem no seu código.
    Se depois adicionar outras, inclua novas linhas.
  */
  theme: {
    extend: {
      colors: {
        slate:   colors.slate,
        gray:    colors.gray,
        stone:   colors.stone,
        neutral: colors.neutral,
        red:     colors.red,
        emerald: colors.emerald,
        /* cor de marca */
        primary: { DEFAULT: '#047857' },
      },
    },
  },

  /*
    Para evitar futuros “unknown utility class” caso alguma
    variação nova (p.ex. bg-gray-950) surja, geramos utilidades
    para QUALQUER tom dessas escalas via safelist regex.
  */
  safelist: [
    {
      pattern:
        /(bg|text|border|ring|stroke|fill|outline)-(slate|gray|stone|neutral|red|emerald)-[0-9]{2,3}/,
    },
  ],

  plugins: [require('@tailwindcss/typography')],
}

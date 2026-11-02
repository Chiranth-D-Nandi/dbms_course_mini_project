// Owner: Person B
import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        railway: {
          blue: '#0B3C5D',
          navy: '#1D2731',
          gold: '#F49F1C',
          light: '#F8F9FA',
          accent: '#328CC1',
          tatkal: '#DC2626',
        },
      },
    },
  },
  plugins: [],
};

export default config;

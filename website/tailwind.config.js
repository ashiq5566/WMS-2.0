module.exports = {
  content: [
    "./components/**/*.{vue,js,ts}",
    "./layouts/**/*.{vue,js,ts}",
    "./pages/**/*.{vue,js,ts}",
    "./app/**/*.{vue,js,ts}",
    "./plugins/**/*.{js,ts}",
    "./nuxt.config.{js,ts}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#3B4A58",
          primaryLight: "#556573",
          accent: "#C9A66B",
          surface: "#F6F6F4",
          text: "#1A1A1A",
          textSoft: "#6B7280",
        },
      },
    },
  },
  plugins: [],
};

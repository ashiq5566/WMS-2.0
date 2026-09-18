import { ref } from 'vue';

export const isDarkMode = ref(false);

export function initTheme() {
  if (typeof window === 'undefined' || typeof document === 'undefined') return;

  const savedTheme = localStorage.getItem('theme');
  const prefersDark =
    window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

  if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
    isDarkMode.value = true;
    document.documentElement.classList.add('dark', 'my-app-dark');
  } else {
    isDarkMode.value = false;
    document.documentElement.classList.remove('dark', 'my-app-dark');
  }
}

export function toggleTheme() {
  if (typeof window === 'undefined' || typeof document === 'undefined') return false;

  isDarkMode.value = !isDarkMode.value;
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark', 'my-app-dark');
    localStorage.setItem('theme', 'dark');
  } else {
    document.documentElement.classList.remove('dark', 'my-app-dark');
    localStorage.setItem('theme', 'light');
  }
  return isDarkMode.value;
}

export function useTheme() {
  return {
    isDarkMode,
    toggleTheme,
    initTheme
  };
}

import { describe, it, expect, beforeEach } from 'vitest';
import { isDarkMode, initTheme, toggleTheme } from '../theme';

describe('Theme Utility', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.className = '';
    isDarkMode.value = false;
  });

  it('should toggle theme from light to dark and back', () => {
    expect(isDarkMode.value).toBe(false);

    toggleTheme();
    expect(isDarkMode.value).toBe(true);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(document.documentElement.classList.contains('my-app-dark')).toBe(true);
    expect(localStorage.getItem('theme')).toBe('dark');

    toggleTheme();
    expect(isDarkMode.value).toBe(false);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(document.documentElement.classList.contains('my-app-dark')).toBe(false);
    expect(localStorage.getItem('theme')).toBe('light');
  });

  it('should initialize dark theme from localStorage', () => {
    localStorage.setItem('theme', 'dark');
    initTheme();
    expect(isDarkMode.value).toBe(true);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
    expect(document.documentElement.classList.contains('my-app-dark')).toBe(true);
  });

  it('should initialize light theme from localStorage', () => {
    localStorage.setItem('theme', 'light');
    initTheme();
    expect(isDarkMode.value).toBe(false);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
    expect(document.documentElement.classList.contains('my-app-dark')).toBe(false);
  });
});

/**
 * BRUTALIST MINIMALISM DESIGN SYSTEM
 * Theme Toggle - Light/Dark Mode with localStorage
 * 
 * Switches body class and saves preference
 */

(function() {
  'use strict';

  // Constants
  const THEME_KEY = 'calnio-theme';
  const DARK_MODE_CLASS = 'dark-mode';
  const THEME_TOGGLE_SELECTOR = '.theme-toggle';
  
  // Theme state
  let isDarkMode = false;

  /**
   * Initialize theme from localStorage or system preference
   */
  function initTheme() {
    // Check localStorage first
    const savedTheme = localStorage.getItem(THEME_KEY);
    
    if (savedTheme === 'dark') {
      isDarkMode = true;
    } else if (savedTheme === 'light') {
      isDarkMode = false;
    } else {
      // Check system preference if no saved theme
      isDarkMode = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    
    applyTheme();
  }

  /**
   * Apply theme by toggling body class
   */
  function applyTheme() {
    if (isDarkMode) {
      document.body.classList.add(DARK_MODE_CLASS);
    } else {
      document.body.classList.remove(DARK_MODE_CLASS);
    }
    
    updateToggleButtons();
  }

  /**
   * Toggle theme between light and dark
   */
  function toggleTheme() {
    isDarkMode = !isDarkMode;
    localStorage.setItem(THEME_KEY, isDarkMode ? 'dark' : 'light');
    applyTheme();
  }

  /**
   * Update all theme toggle buttons text
   */
  function updateToggleButtons() {
    const toggleButtons = document.querySelectorAll(THEME_TOGGLE_SELECTOR);
    toggleButtons.forEach(button => {
      // Check if button is in mobile nav (has nav-mobile-link class)
      if (button.classList.contains('nav-mobile-link')) {
        button.textContent = isDarkMode ? 'LIGHT MODE' : 'DARK MODE';
      } else {
        button.textContent = isDarkMode ? 'LIGHT' : 'DARK';
      }
      button.setAttribute('aria-label', `Switch to ${isDarkMode ? 'light' : 'dark'} mode`);
    });
  }

  /**
   * Setup event listeners for theme toggle buttons
   */
  function setupEventListeners() {
    const toggleButtons = document.querySelectorAll(THEME_TOGGLE_SELECTOR);
    toggleButtons.forEach(button => {
      button.addEventListener('click', toggleTheme);
    });
  }

  /**
   * Initialize on DOM ready
   */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      initTheme();
      setupEventListeners();
    });
  } else {
    initTheme();
    setupEventListeners();
  }

  // Listen for system theme changes
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
      // Only update if user hasn't manually set a preference
      if (!localStorage.getItem(THEME_KEY)) {
        isDarkMode = e.matches;
        applyTheme();
      }
    });
  }

  // Expose toggle function globally for manual calls
  window.calnioThemeToggle = toggleTheme;

})();

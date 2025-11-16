/**
 * BRUTALIST MINIMALISM DESIGN SYSTEM
 * Burger Menu - Mobile Navigation Toggle
 * 
 * Simple toggle for mobile navigation overlay
 */

(function() {
  'use strict';

  // Constants
  const BURGER_SELECTOR = '.burger-menu';
  const OVERLAY_SELECTOR = '.nav-mobile-overlay';
  const ACTIVE_CLASS = 'active';
  const BODY_LOCK_CLASS = 'nav-open';

  /**
   * Toggle mobile navigation
   */
  function toggleNav() {
    const burger = document.querySelector(BURGER_SELECTOR);
    const overlay = document.querySelector(OVERLAY_SELECTOR);
    
    if (!burger || !overlay) return;
    
    const isActive = burger.classList.contains(ACTIVE_CLASS);
    
    if (isActive) {
      // Close navigation
      burger.classList.remove(ACTIVE_CLASS);
      overlay.classList.remove(ACTIVE_CLASS);
      document.body.classList.remove(BODY_LOCK_CLASS);
    } else {
      // Open navigation
      burger.classList.add(ACTIVE_CLASS);
      overlay.classList.add(ACTIVE_CLASS);
      document.body.classList.add(BODY_LOCK_CLASS);
    }
  }

  /**
   * Close navigation
   */
  function closeNav() {
    const burger = document.querySelector(BURGER_SELECTOR);
    const overlay = document.querySelector(OVERLAY_SELECTOR);
    
    if (!burger || !overlay) return;
    
    burger.classList.remove(ACTIVE_CLASS);
    overlay.classList.remove(ACTIVE_CLASS);
    document.body.classList.remove(BODY_LOCK_CLASS);
  }

  /**
   * Setup event listeners
   */
  function setupEventListeners() {
    // Burger button click
    const burger = document.querySelector(BURGER_SELECTOR);
    if (burger) {
      burger.addEventListener('click', toggleNav);
    }
    
    // Close on link click
    const overlay = document.querySelector(OVERLAY_SELECTOR);
    if (overlay) {
      const links = overlay.querySelectorAll('a');
      links.forEach(link => {
        link.addEventListener('click', closeNav);
      });
    }
    
    // Close on Escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        closeNav();
      }
    });
    
    // Close on window resize to desktop
    window.addEventListener('resize', function() {
      if (window.innerWidth > 968) {
        closeNav();
      }
    });
  }

  /**
   * Initialize on DOM ready
   */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupEventListeners);
  } else {
    setupEventListeners();
  }

  // Expose functions globally
  window.calnioNav = {
    toggle: toggleNav,
    close: closeNav
  };

})();

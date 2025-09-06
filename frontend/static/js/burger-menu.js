/**
 * Burger Menu JavaScript
 * Handles the burger menu toggle functionality
 */

document.addEventListener("DOMContentLoaded", function () {
  const burgerMenu = document.querySelector(".burger-menu");
  const menuOverlay = document.querySelector(".menu-overlay");
  const body = document.body;

  if (!burgerMenu || !menuOverlay) {
    console.warn("Burger menu elements not found");
    return;
  }

  // Toggle menu function
  function toggleMenu() {
    const isActive = burgerMenu.classList.contains("active");

    if (isActive) {
      // Close menu
      closeMenu();
    } else {
      // Open menu
      openMenu();
    }
  }

  // Open menu function
  function openMenu() {
    burgerMenu.classList.add("active");
    menuOverlay.classList.add("active");
    body.classList.add("menu-open");

    // Prevent body scroll
    body.style.overflow = "hidden";
  }

  // Close menu function
  function closeMenu() {
    burgerMenu.classList.remove("active");
    menuOverlay.classList.add("closing");

    // Remove closing class after animation
    setTimeout(() => {
      menuOverlay.classList.remove("active", "closing");
      body.classList.remove("menu-open");
      body.style.overflow = "";
    }, 300);
  }

  // Event listeners
  burgerMenu.addEventListener("click", toggleMenu);

  // Close menu when clicking on overlay (not on links)
  menuOverlay.addEventListener("click", function (e) {
    if (e.target === menuOverlay) {
      closeMenu();
    }
  });

  // Close menu when clicking on navigation links
  const navLinks = document.querySelectorAll(".mobile-nav .nav-link");
  navLinks.forEach((link) => {
    link.addEventListener("click", closeMenu);
  });

  // Close menu on escape key
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && menuOverlay.classList.contains("active")) {
      closeMenu();
    }
  });

  // Handle window resize
  window.addEventListener("resize", function () {
    if (window.innerWidth > 768 && menuOverlay.classList.contains("active")) {
      closeMenu();
    }
  });

  // Handle orientation change on mobile
  window.addEventListener("orientationchange", function () {
    setTimeout(() => {
      if (window.innerWidth > 768 && menuOverlay.classList.contains("active")) {
        closeMenu();
      }
    }, 100);
  });
});

/**
 * Utility function to programmatically open/close menu
 * Can be used from other scripts if needed
 */
window.BurgerMenu = {
  open: function () {
    const burgerMenu = document.querySelector(".burger-menu");
    const menuOverlay = document.querySelector(".menu-overlay");
    const body = document.body;

    if (burgerMenu && menuOverlay) {
      burgerMenu.classList.add("active");
      menuOverlay.classList.add("active");
      body.classList.add("menu-open");
      body.style.overflow = "hidden";
    }
  },

  close: function () {
    const burgerMenu = document.querySelector(".burger-menu");
    const menuOverlay = document.querySelector(".menu-overlay");
    const body = document.body;

    if (burgerMenu && menuOverlay) {
      burgerMenu.classList.remove("active");
      menuOverlay.classList.add("closing");

      setTimeout(() => {
        menuOverlay.classList.remove("active", "closing");
        body.classList.remove("menu-open");
        body.style.overflow = "";
      }, 300);
    }
  },

  toggle: function () {
    const burgerMenu = document.querySelector(".burger-menu");
    if (burgerMenu) {
      burgerMenu.click();
    }
  },
};

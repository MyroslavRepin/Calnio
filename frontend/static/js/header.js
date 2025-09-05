// Enhanced Header functionality for responsive navigation with full-screen overlay
document.addEventListener("DOMContentLoaded", function () {
  const burgerMenu = document.getElementById("burger-menu");
  const navMobile = document.getElementById("nav-mobile");
  const closeMenuBtn = document.getElementById("close-menu-btn");
  const body = document.body;
  const header = document.querySelector(".header");

  // Animation direction preference (can be changed to 'top' for slide from top)
  const animationDirection = "right"; // 'right' or 'top'

  // Toggle mobile menu with enhanced animations
  function toggleMobileMenu() {
    const isActive = burgerMenu.classList.contains("active");

    if (isActive) {
      closeMobileMenu();
    } else {
      openMobileMenu();
    }
  }

  // Open mobile menu with smooth animations
  function openMobileMenu() {
    // Set animation direction
    if (animationDirection === "top") {
      navMobile.classList.add("slide-from-top");
    }

    // Show overlay
    navMobile.style.display = "flex";

    // Force reflow to ensure display change is applied
    navMobile.offsetHeight;

    // Add active class for animation
    burgerMenu.classList.add("active");
    navMobile.classList.add("active");

    // Prevent background scrolling
    body.style.overflow = "hidden";
    body.style.position = "fixed";
    body.style.width = "100%";

    // Add header scrolled effect
    header.classList.add("scrolled");
  }

  // Close mobile menu with smooth animations
  function closeMobileMenu() {
    // Remove active classes
    burgerMenu.classList.remove("active");
    navMobile.classList.remove("active");

    // Remove animation direction class
    navMobile.classList.remove("slide-from-top");

    // Restore body scrolling
    body.style.overflow = "";
    body.style.position = "";
    body.style.width = "";

    // Hide overlay after animation completes
    setTimeout(() => {
      if (!navMobile.classList.contains("active")) {
        navMobile.style.display = "none";
      }
    }, 400); // Match CSS transition duration
  }

  // Close mobile menu when clicking on a link
  function closeMobileMenuOnLinkClick() {
    closeMobileMenu();
  }

  // Event listeners
  if (burgerMenu) {
    burgerMenu.addEventListener("click", toggleMobileMenu);
  }

  if (closeMenuBtn) {
    closeMenuBtn.addEventListener("click", closeMobileMenu);
  }

  // Close menu when clicking on mobile nav links
  const mobileNavLinks = document.querySelectorAll(".nav-link-mobile");
  mobileNavLinks.forEach((link) => {
    link.addEventListener("click", closeMobileMenuOnLinkClick);
  });

  // Close menu when clicking outside the overlay
  document.addEventListener("click", function (event) {
    const isClickInsideOverlay = event.target.closest(".nav-mobile");
    const isBurgerMenu = event.target.closest("#burger-menu");
    const isCloseButton = event.target.closest("#close-menu-btn");

    if (
      !isClickInsideOverlay &&
      !isBurgerMenu &&
      !isCloseButton &&
      navMobile.classList.contains("active")
    ) {
      closeMobileMenu();
    }
  });

  // Close menu on escape key
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && navMobile.classList.contains("active")) {
      closeMobileMenu();
    }
  });

  // Handle window resize - close mobile menu on desktop
  window.addEventListener("resize", function () {
    if (window.innerWidth > 768 && navMobile.classList.contains("active")) {
      closeMobileMenu();
    }
  });

  // Prevent body scroll when overlay is open (additional safety)
  document.addEventListener(
    "touchmove",
    function (event) {
      if (navMobile.classList.contains("active")) {
        event.preventDefault();
      }
    },
    { passive: false }
  );

  // Smooth scroll for anchor links (if any)
  const anchorLinks = document.querySelectorAll('a[href^="#"]');
  anchorLinks.forEach((link) => {
    link.addEventListener("click", function (e) {
      const href = this.getAttribute("href");
      if (href === "#") return;

      e.preventDefault();
      const target = document.querySelector(href);
      if (target) {
        const headerHeight = document.querySelector(".header").offsetHeight;
        const targetPosition = target.offsetTop - headerHeight - 20;

        window.scrollTo({
          top: targetPosition,
          behavior: "smooth",
        });

        // Close mobile menu if open
        if (navMobile.classList.contains("active")) {
          closeMobileMenu();
        }
      }
    });
  });

  // Enhanced scroll effect for header with glassmorphism
  let lastScrollTop = 0;
  let ticking = false;

  function updateHeaderOnScroll() {
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;

    // Add/remove scrolled class for glassmorphism effect
    if (scrollTop > 50) {
      header.classList.add("scrolled");
    } else {
      header.classList.remove("scrolled");
    }

    lastScrollTop = scrollTop;
    ticking = false;
  }

  window.addEventListener("scroll", function () {
    if (!ticking) {
      requestAnimationFrame(updateHeaderOnScroll);
      ticking = true;
    }
  });
});

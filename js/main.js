/* js/main.js */
document.addEventListener("DOMContentLoaded", () => {
  // 1. Reveal Animations on Scroll
  const revealElements = document.querySelectorAll(
    ".section-title, .section-description, .stat-card, .trust-item, .game-embed-container, .benefit-item, .faq-item",
  );

  revealElements.forEach((el, index) => {
    el.classList.add("reveal-up");
    // Add staggered delays for items in a grid/list
    if (el.classList.contains("trust-item")) {
      el.classList.add(`delay-${((index % 3) + 1) * 100}`);
    }
  });

  const observerOptions = {
    root: null,
    rootMargin: "0px",
    threshold: 0.15,
  };

  const revealObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll(".reveal-up").forEach((el) => {
    revealObserver.observe(el);
  });

  // 2. Header Scroll Effect
  const header = document.getElementById("header");

  window.addEventListener("scroll", () => {
    if (window.scrollY > 50) {
      header.classList.add("scrolled");
    } else {
      header.classList.remove("scrolled");
    }
  });

  // 3. Mobile Menu Toggle
  const mobileToggle = document.querySelector(".mobile-toggle");
  const nav = document.querySelector(".nav");

  if (mobileToggle && nav) {
    mobileToggle.addEventListener("click", () => {
      nav.classList.toggle("active");
      // Toggle hamburger to cross animation
      const spans = mobileToggle.querySelectorAll("span");
      if (nav.classList.contains("active")) {
        spans[0].style.transform = "rotate(45deg) translate(5px, 5px)";
        spans[1].style.opacity = "0";
        spans[2].style.transform = "rotate(-45deg) translate(7px, -8px)";
      } else {
        spans[0].style.transform = "none";
        spans[1].style.opacity = "1";
        spans[2].style.transform = "none";
      }
    });
  }

  // 4. Smooth Scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", function (e) {
      e.preventDefault();

      // Close mobile menu if open
      if (nav && nav.classList.contains("active")) {
        mobileToggle.click();
      }

      const targetId = this.getAttribute("href");
      if (targetId === "#") return;

      const targetElement = document.querySelector(targetId);
      if (targetElement) {
        const headerHeight = document.querySelector(".header").offsetHeight;
        const targetPosition =
          targetElement.getBoundingClientRect().top +
          window.scrollY -
          headerHeight;

        window.scrollTo({
          top: targetPosition,
          behavior: "smooth",
        });
      }
    });
  });

  // 5. Counter Animation for the coupons
  const couponsEl = document.getElementById("coupons-left");
  if (couponsEl) {
    let startTimestamp = null;
    const duration = 2500;
    const finalValue = 1243;

    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);

      // easeOutExpo
      const easeOut = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);

      const currentValue = Math.floor(easeOut * finalValue);

      // Format with thousand separator
      couponsEl.innerText = currentValue
        .toString()
        .replace(/\B(?=(\d{3})+(?!\d))/g, ".");

      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        couponsEl.innerText = "1.243";
      }
    };

    const counterObserver = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        window.requestAnimationFrame(step);
        counterObserver.disconnect();
      }
    });

    counterObserver.observe(couponsEl);
  }
});

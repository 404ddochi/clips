(function () {
  "use strict";

  function initHeader() {
    const header = document.querySelector("[data-header]");
    if (!header) return;

    const onScroll = function () {
      header.classList.toggle("is-scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  function initMobileNav() {
    const header = document.querySelector("[data-header]");
    const toggle = document.querySelector("[data-nav-toggle]");
    const nav = document.querySelector("[data-primary-nav]");
    const backdrop = document.querySelector("[data-nav-backdrop]");
    if (!header || !toggle || !nav) return;

    const focusableSelector =
      'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

    function setOpen(open) {
      header.classList.toggle("is-nav-open", open);
      document.body.classList.toggle("is-nav-open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
      toggle.querySelector(".nav-toggle-label").textContent = open
        ? "메뉴 닫기"
        : "메뉴 열기";
      const openIcon = toggle.querySelector("[data-nav-icon-open]");
      const closeIcon = toggle.querySelector("[data-nav-icon-close]");
      if (openIcon && closeIcon) {
        openIcon.classList.toggle("is-hidden", open);
        closeIcon.classList.toggle("is-hidden", !open);
      }
      if (backdrop) {
        if (open) {
          backdrop.removeAttribute("hidden");
        } else {
          backdrop.setAttribute("hidden", "");
        }
      }
      if (open) {
        const first = nav.querySelector(focusableSelector);
        if (first instanceof HTMLElement) {
          first.focus();
        }
      }
    }

    function closeNav() {
      setOpen(false);
    }

    toggle.addEventListener("click", function () {
      const willOpen = !header.classList.contains("is-nav-open");
      setOpen(willOpen);
    });

    nav.querySelectorAll("a").forEach(function (link) {
      link.addEventListener("click", closeNav);
    });

    if (backdrop) {
      backdrop.addEventListener("click", closeNav);
    }

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && header.classList.contains("is-nav-open")) {
        event.preventDefault();
        closeNav();
        toggle.focus();
      }
    });

    document.addEventListener("click", function (event) {
      if (!header.classList.contains("is-nav-open")) return;
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (header.contains(target)) return;
      closeNav();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initHeader();
      initMobileNav();
    });
  } else {
    initHeader();
    initMobileNav();
  }
})();

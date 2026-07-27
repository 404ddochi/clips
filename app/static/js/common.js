(function () {
  const header = document.querySelector("[data-header]");
  const toggle = document.querySelector("[data-nav-toggle]");
  const nav = document.querySelector("[data-primary-nav]");

  if (header) {
    const onScroll = () => {
      header.classList.toggle("is-scrolled", window.scrollY > 8);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  if (toggle && header && nav) {
    toggle.addEventListener("click", () => {
      const open = header.classList.toggle("is-nav-open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });

    nav.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        header.classList.remove("is-nav-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }
})();

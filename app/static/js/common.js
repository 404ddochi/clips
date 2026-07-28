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

  function fallbackCopyText(text) {
    return new Promise(function (resolve, reject) {
      const area = document.createElement("textarea");
      area.value = text;
      area.setAttribute("readonly", "");
      area.setAttribute("aria-hidden", "true");
      area.style.position = "fixed";
      area.style.top = "-9999px";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.focus();
      area.select();
      area.setSelectionRange(0, area.value.length);
      try {
        const ok = document.execCommand("copy");
        document.body.removeChild(area);
        if (ok) {
          resolve();
        } else {
          reject(new Error("copy failed"));
        }
      } catch (error) {
        document.body.removeChild(area);
        reject(error);
      }
    });
  }

  function copyTextToClipboard(text) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      return navigator.clipboard.writeText(text).catch(function () {
        return fallbackCopyText(text);
      });
    }
    return fallbackCopyText(text);
  }

  function initCopyButtons() {
    const buttons = document.querySelectorAll("[data-copy-text]");
    if (!buttons.length) return;

    buttons.forEach(function (button) {
      if (!(button instanceof HTMLButtonElement)) return;

      button.addEventListener("click", function () {
        if (button.disabled) return;
        const text = button.getAttribute("data-copy-text");
        if (!text) return;

        const labelEl = button.querySelector("[data-copy-label]");
        const labelShortEl = button.querySelector("[data-copy-label-short]");
        const defaultLabel =
          button.getAttribute("data-copy-label-default") || "코드 복사";
        const successLabel =
          button.getAttribute("data-copy-label-success") || "복사 완료";
        const defaultShort =
          button.getAttribute("data-copy-label-default-short") || defaultLabel;
        const successShort =
          button.getAttribute("data-copy-label-success-short") || successLabel;

        function setCopyLabels(fullText, shortText) {
          if (labelEl) {
            labelEl.textContent = fullText;
          }
          if (labelShortEl) {
            labelShortEl.textContent = shortText;
          }
        }

        copyTextToClipboard(text)
          .then(function () {
            button.classList.add("is-copied");
            setCopyLabels(successLabel, successShort);
            const previousTimer = button.dataset.copyTimerId;
            if (previousTimer) {
              window.clearTimeout(Number(previousTimer));
            }
            const timerId = window.setTimeout(function () {
              button.classList.remove("is-copied");
              setCopyLabels(defaultLabel, defaultShort);
              delete button.dataset.copyTimerId;
            }, 1800);
            button.dataset.copyTimerId = String(timerId);
          })
          .catch(function () {
            button.classList.remove("is-copied");
            setCopyLabels(defaultLabel, defaultShort);
          });
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      initHeader();
      initMobileNav();
      initCopyButtons();
    });
  } else {
    initHeader();
    initMobileNav();
    initCopyButtons();
  }
})();

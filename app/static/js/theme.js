/**
 * CLIPS theme controller (system | light | dark)
 * Storage key: clips-theme
 */
(function (global) {
  "use strict";

  var STORAGE_KEY = "clips-theme";
  var PREFERENCES = { system: true, light: true, dark: true };

  function readStoredPreference() {
    try {
      var value = global.localStorage.getItem(STORAGE_KEY);
      if (value && PREFERENCES[value]) return value;
    } catch (_err) {
      /* private mode / blocked storage */
    }
    return "system";
  }

  function writeStoredPreference(preference) {
    try {
      global.localStorage.setItem(STORAGE_KEY, preference);
      return true;
    } catch (_err) {
      return false;
    }
  }

  function systemTheme() {
    try {
      return global.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    } catch (_err) {
      return "dark";
    }
  }

  function resolveTheme(preference) {
    var pref = PREFERENCES[preference] ? preference : "system";
    return pref === "system" ? systemTheme() : pref;
  }

  function preferenceLabel(preference) {
    if (preference === "light") return "라이트 모드";
    if (preference === "dark") return "다크 모드";
    return "시스템 설정";
  }

  function applyTheme(preference) {
    var pref = PREFERENCES[preference] ? preference : "system";
    var resolved = resolveTheme(pref);
    var root = document.documentElement;
    root.setAttribute("data-theme", resolved);
    root.setAttribute("data-theme-preference", pref);
    root.style.colorScheme = resolved;

    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) {
      var themeColor = getComputedStyle(root).getPropertyValue("--theme-color").trim();
      if (themeColor) meta.setAttribute("content", themeColor);
    }
    return { preference: pref, theme: resolved };
  }

  function syncControl(control, preference, theme) {
    if (!control) return;
    var toggle = control.querySelector("[data-theme-toggle]");
    var label = control.querySelector("[data-theme-label]");
    var icons = control.querySelectorAll("[data-theme-icon]");
    var options = control.querySelectorAll("[data-theme-option]");

    if (label) {
      label.textContent = "테마 설정, 현재 " + preferenceLabel(preference);
    }
    if (toggle) {
      toggle.setAttribute(
        "aria-label",
        "테마 설정, 현재 " + preferenceLabel(preference),
      );
    }

    icons.forEach(function (icon) {
      var name = icon.getAttribute("data-theme-icon");
      var show =
        (preference === "system" && name === "system") ||
        (preference === "light" && name === "light") ||
        (preference === "dark" && name === "dark");
      icon.hidden = !show;
      icon.classList.toggle("is-hidden", !show);
    });

    options.forEach(function (option) {
      var value = option.getAttribute("data-theme-option");
      var selected = value === preference;
      option.setAttribute("aria-checked", selected ? "true" : "false");
      option.classList.toggle("is-selected", selected);
      var check = option.querySelector("[data-theme-check]");
      if (check) check.hidden = !selected;
    });

    control.setAttribute("data-resolved-theme", theme);
  }

  function setMenuOpen(control, open) {
    var toggle = control.querySelector("[data-theme-toggle]");
    var menu = control.querySelector("[data-theme-menu]");
    if (!toggle || !menu) return;
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    if (open) {
      menu.removeAttribute("hidden");
    } else {
      menu.setAttribute("hidden", "");
    }
    control.classList.toggle("is-open", open);
  }

  function initThemeControl() {
    var control = document.querySelector("[data-theme-control]");
    var preference = readStoredPreference();
    var applied = applyTheme(preference);
    syncControl(control, applied.preference, applied.theme);

    if (!control) return;

    var toggle = control.querySelector("[data-theme-toggle]");
    var menu = control.querySelector("[data-theme-menu]");
    if (!toggle || !menu) return;

    toggle.addEventListener("click", function (event) {
      event.stopPropagation();
      var open = toggle.getAttribute("aria-expanded") !== "true";
      setMenuOpen(control, open);
    });

    menu.querySelectorAll("[data-theme-option]").forEach(function (option) {
      option.addEventListener("click", function (event) {
        event.stopPropagation();
        var next = option.getAttribute("data-theme-option") || "system";
        writeStoredPreference(next);
        var result = applyTheme(next);
        syncControl(control, result.preference, result.theme);
        setMenuOpen(control, false);
        toggle.focus();
      });
    });

    document.addEventListener("keydown", function (event) {
      if (event.key !== "Escape") return;
      if (toggle.getAttribute("aria-expanded") !== "true") return;
      event.preventDefault();
      setMenuOpen(control, false);
      toggle.focus();
    });

    document.addEventListener("click", function (event) {
      if (toggle.getAttribute("aria-expanded") !== "true") return;
      var target = event.target;
      if (!(target instanceof Node)) return;
      if (control.contains(target)) return;
      setMenuOpen(control, false);
    });

    try {
      var media = global.matchMedia("(prefers-color-scheme: dark)");
      var onChange = function () {
        var current = readStoredPreference();
        if (current !== "system") return;
        var result = applyTheme("system");
        syncControl(control, result.preference, result.theme);
      };
      if (typeof media.addEventListener === "function") {
        media.addEventListener("change", onChange);
      } else if (typeof media.addListener === "function") {
        media.addListener(onChange);
      }
    } catch (_err) {
      /* ignore */
    }
  }

  global.CLIPSTheme = {
    STORAGE_KEY: STORAGE_KEY,
    readStoredPreference: readStoredPreference,
    writeStoredPreference: writeStoredPreference,
    resolveTheme: resolveTheme,
    applyTheme: applyTheme,
    preferenceLabel: preferenceLabel,
    initThemeControl: initThemeControl,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initThemeControl);
  } else {
    initThemeControl();
  }
})(window);

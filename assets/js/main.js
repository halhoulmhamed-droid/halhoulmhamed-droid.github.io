(() => {
  "use strict";

  // Enhancement starts only once this file loads. Without JavaScript, all
  // navigation links remain visible, including on narrow screens.
  document.documentElement.classList.add("js");

  const toggle = document.querySelector("[data-nav-toggle]");
  const nav = document.querySelector("[data-site-nav]");

  if (toggle && nav) {
    const desktop = window.matchMedia("(min-width: 801px)");
    const setOpen = (open) => {
      toggle.setAttribute("aria-expanded", String(open));
      nav.classList.toggle("is-open", open);
    };
    const closeMenu = () => setOpen(false);

    toggle.addEventListener("click", () => {
      setOpen(toggle.getAttribute("aria-expanded") !== "true");
    });

    nav.addEventListener("click", (event) => {
      if (event.target.closest("a")) closeMenu();
    });

    document.addEventListener("click", (event) => {
      if (
        toggle.getAttribute("aria-expanded") === "true" &&
        !toggle.contains(event.target) &&
        !nav.contains(event.target)
      ) closeMenu();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        closeMenu();
        toggle.focus();
      }
    });

    if (typeof desktop.addEventListener === "function") {
      desktop.addEventListener("change", closeMenu);
    } else {
      desktop.addListener(closeMenu);
    }
  }

  // Explicit static counterpart links always work. Preserve the currently
  // consulted section and query when switching language, without redirects.
  const updateLanguageLinks = () => {
    document.querySelectorAll("[data-language-link]").forEach((link) => {
      const destination = new URL(link.href, window.location.href);
      if (destination.origin === window.location.origin) {
        destination.search = window.location.search;
        destination.hash = window.location.hash;
        link.href = destination.href;
      }
    });
  };
  updateLanguageLinks();
  window.addEventListener("hashchange", updateLanguageLinks);

  document.querySelectorAll("[data-year]").forEach((node) => {
    node.textContent = String(new Date().getFullYear());
  });
})();

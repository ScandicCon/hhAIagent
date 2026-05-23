(function () {
  const toggle = document.querySelector(".menu-toggle");
  const mobileNav = document.querySelector(".nav-mobile");
  if (!toggle || !mobileNav) return;

  function setOpen(open) {
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    mobileNav.classList.toggle("is-open", open);
    document.body.style.overflow = open ? "hidden" : "";
  }

  toggle.addEventListener("click", function () {
    setOpen(toggle.getAttribute("aria-expanded") !== "true");
  });

  mobileNav.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      setOpen(false);
    });
  });
})();

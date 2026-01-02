document.addEventListener("DOMContentLoaded", function () {
  /* ===============================
     TRANSLATION HANDLER
  =============================== */
  const TRANSLATIONS = window.TRANSLATIONS || {};
  const CURRENT_LANG = window.CURRENT_LANG || "id";

  function t(key, params = {}) {
    let msg = TRANSLATIONS?.[CURRENT_LANG]?.[key] || key;

    Object.keys(params).forEach((k) => {
      msg = msg.replaceAll(`{${k}}`, params[k]);
    });

    return msg;
  }

  /* ===============================
     SMOOTH SCROLL
  =============================== */
  $('a[href^="#"]').on("click", function (e) {
    e.preventDefault();
    const target = this.hash;
    const $target = $(target);

    $("html, body")
      .stop()
      .animate({ scrollTop: $target.offset().top }, 1300, "easeInOutExpo");
  });

  /* ===============================
     HEADER TRANSPARENCY
  =============================== */
  window.addEventListener("scroll", function () {
    const header = document.getElementById("main-header");
    if (!header) return;

    if (window.scrollY > 10) {
      header.classList.remove("bg-opacity-100");
      header.classList.add("bg-opacity-30");
    } else {
      header.classList.remove("bg-opacity-30");
      header.classList.add("bg-opacity-100");
    }
  });

  /* ===============================
     FLIP CARD INTERACTION
  =============================== */
  const cards = document.querySelectorAll(".card-inner");

  cards.forEach((card) => {
    card.addEventListener("click", function (e) {
      cards.forEach((c) => {
        if (c !== card) c.classList.remove("rotate-y-180");
      });
      card.classList.toggle("rotate-y-180");
      e.stopPropagation();
    });
  });

  document.querySelectorAll(".card-inner a").forEach((link) => {
    link.addEventListener("click", (e) => e.stopPropagation());
  });

  document.addEventListener("click", function () {
    cards.forEach((card) => card.classList.remove("rotate-y-180"));
  });

  /* ===============================
     IMAGE SLIDER (AUTO)
  =============================== */
  const images = [
    document.getElementById("img1"),
    document.getElementById("img2"),
    document.getElementById("img3"),
  ].filter(Boolean);

  const fadeOverlay = document.getElementById("colorFade");
  let currentIndex = 0;

  function showNextImage() {
    if (!images.length || !fadeOverlay) return;

    fadeOverlay.classList.add("show");

    setTimeout(() => {
      images.forEach((img) => img.classList.remove("active"));
      currentIndex = (currentIndex + 1) % images.length;
      images[currentIndex].classList.add("active");
      fadeOverlay.classList.remove("show");
    }, 1000);
  }

  if (images.length > 1) {
    setInterval(showNextImage, 4000);
  }

  /* ===============================
     FORM VALIDATION
  =============================== */
  const form = document.querySelector("form");

  if (form) {
    form.addEventListener("submit", function (e) {
      const email = document.getElementById("email")?.value || "";
      let nomor_hp = document.getElementById("nomor_hp")?.value || "";
      const btn = document.getElementById("submitBtn");

      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      const hpRegex = /^(08\d{8,11}|\+628\d{7,10})$/;

      const validPrefixes = [
        "0811",
        "0812",
        "0813",
        "0821",
        "0822",
        "0823",
        "0851",
        "0852",
        "0853",
        "0817",
        "0818",
        "0819",
        "0857",
        "0858",
        "0896",
        "0897",
        "0898",
        "0899",
      ];

      if (!emailRegex.test(email)) {
        e.preventDefault();
        showError(t("invalid_email_format"));
        return;
      }

      if (nomor_hp.startsWith("+62")) {
        nomor_hp = "0" + nomor_hp.slice(3);
      }

      if (!hpRegex.test(nomor_hp)) {
        e.preventDefault();
        showError(t("invalid_phone_format"));
        return;
      }

      const prefix = nomor_hp.substring(0, 4);
      if (!validPrefixes.includes(prefix)) {
        e.preventDefault();
        showError(t("invalid_phone_prefix"));
        return;
      }

      if (/^(0+|08[0-9]{7}1234|08[0-9]{9}000)$/.test(nomor_hp)) {
        e.preventDefault();
        showError(t("invalid_phone_number"));
        return;
      }

      if (btn) {
        btn.disabled = true;
        btn.innerText = "Mengirim...";
      }
    });
  }

  /* ===============================
     ERROR OVERLAY
  =============================== */
  function showError(message) {
    const overlay = document.getElementById("overlay-error");
    const errorMsg = document.getElementById("error-message");

    if (!overlay || !errorMsg) return;

    errorMsg.textContent = message;
    overlay.classList.remove("hidden");
    overlay.classList.add("flex");
    document.body.classList.add("blurred", "overflow-hidden");
  }

  window.closeError = function () {
    const overlay = document.getElementById("overlay-error");
    if (!overlay) return;

    overlay.classList.remove("flex");
    overlay.classList.add("hidden");
    document.body.classList.remove("blurred", "overflow-hidden");
  };
});

/* ===============================
   GLOBAL FLASH CLOSE
=============================== */
window.closeFlashAndShowNotifBox = function (element) {
  const flashOverlay = element.closest(".flash-wrapper");
  if (flashOverlay) flashOverlay.classList.add("hidden");
};

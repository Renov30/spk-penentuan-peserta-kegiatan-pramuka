function redirectToLoginWithGoogle() {
  const offlineAlert = document.getElementById("offline-alert");

  // Jika user sedang offline
  if (!navigator.onLine) {
    if (offlineAlert) {
      offlineAlert.classList.remove("hidden");
    }
    return;
  }
  let next = window.location.pathname + window.location.search;

  // Hindari redirect loop ke halaman login
  if (next === "/login" || next === "/login/") {
    next = "";
  }

  // Bangun URL login Google
  const url = next
    ? `/login/google/?next=${encodeURIComponent(next)}`
    : `/login/google/`;
  window.location.href = url;
}

// Sembunyikan pesan offline jika koneksi kembali normal
window.addEventListener("online", () => {
  const offlineAlert = document.getElementById("offline-alert");
  if (offlineAlert) {
    offlineAlert.classList.add("hidden");
  }
});

// (Opsional) Debug saat user offline
window.addEventListener("offline", () => {
  console.warn("User sedang offline");
});

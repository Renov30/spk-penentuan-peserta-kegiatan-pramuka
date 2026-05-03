function redirectToLoginWithGoogle() {
  const offlineAlert = document.getElementById("offline-alert");

  if (!navigator.onLine) {
    if (offlineAlert) {
      offlineAlert.classList.remove("hidden");
    }
    return;
  }

  // 🔥 AMBIL next DARI HIDDEN INPUT (login.html)
  const nextInput = document.querySelector('input[name="next"]');
  let next = nextInput ? nextInput.value : "";

  // fallback terakhir
  if (!next) {
    next = window.location.pathname + window.location.search;
  }

  // Hindari redirect loop ke halaman login
  if (next === "/login" || next === "/login/") {
    next = "";
  }

  // Gunakan window.location.pathname untuk mendeteksi subfolder secara otomatis
  const base = window.location.pathname.includes('/saringpramuka') ? '/saringpramuka' : '';

  const url = next
    ? `${base}/login/google/?next=${encodeURIComponent(next)}`
    : `${base}/login/google/`;


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

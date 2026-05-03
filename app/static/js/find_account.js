document.addEventListener("DOMContentLoaded", function () {
  const toggleButton = document.getElementById("toggleButton");
  const desc = document.getElementById("description");
  const label = document.getElementById("label-email-or-hp");
  const input = document.getElementById("input-email-or-hp");

  // Guard: pastikan elemen ada (aman jika JS dimuat di halaman lain)
  if (!toggleButton || !desc || !label || !input) return;

  // Ambil status terakhir dari localStorage
  let usingPhone = localStorage.getItem("usePhone") === "true";

  // Update tampilan UI
  function updateUI() {
    if (usingPhone) {
      desc.textContent =
        "Masukkan username dan nomor HP Anda untuk mencari akun Anda.";
      label.textContent = "Nomor HP:";
      label.setAttribute("for", "no-hp");
      input.setAttribute("type", "text");
      input.setAttribute("name", "no-hp");
      input.setAttribute("placeholder", "Masukkan nomor HP Anda");
      toggleButton.textContent = "Cari Menggunakan Email";
    } else {
      desc.textContent =
        "Masukkan username dan email Anda untuk mencari akun Anda.";
      label.textContent = "Email:";
      label.setAttribute("for", "email");
      input.setAttribute("type", "email");
      input.setAttribute("name", "email");
      input.setAttribute("placeholder", "Masukkan email");
      toggleButton.textContent = "Cari Menggunakan Nomor HP";
    }
  }

  // Jalankan saat halaman dimuat
  updateUI();

  // Toggle mode pencarian
  toggleButton.addEventListener("click", function () {
    usingPhone = !usingPhone;
    localStorage.setItem("usePhone", usingPhone);
    updateUI();
  });
});

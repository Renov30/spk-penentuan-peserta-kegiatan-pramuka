document.addEventListener("DOMContentLoaded", () => {
  /* =========================
   * Toggle Status Akun User
   * ========================= */
  window.toggleUserStatus = async function (
    userId,
    currentStatus,
    username,
    buttonElement
  ) {
    const isAktif = currentStatus.toLowerCase() === "aktif";
    const newStatus = isAktif ? "non-aktif" : "aktif";

    const statusText = newStatus === "aktif" ? "mengaktifkan" : "menonaktifkan";

    const confirmMessage = `{{ 'Apakah Anda yakin ingin ' if current_lang == 'id' else 'Are you sure you want to ' }}${statusText} akun ${username}?`;

    if (!confirm(confirmMessage)) return;

    // Ambil Alpine component
    const alpineComponent =
      window.Alpine && buttonElement
        ? Alpine.$data(buttonElement.closest("[x-data]"))
        : null;

    if (alpineComponent) alpineComponent.loading = true;

    try {
      // CSRF Token
      const csrfToken =
        document
          .querySelector('meta[name="csrf-token"]')
          ?.getAttribute("content") ||
        document.querySelector('input[name="csrf_token"]')?.value;

      const response = await fetch(`/api/user/update_status/${userId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify({ status: newStatus }),
      });

      const data = await response.json();

      if (data.success) {
        if (alpineComponent) {
          alpineComponent.currentStatus = newStatus;
          alpineComponent.loading = false;
        }

        showNotification(
          data.message || `Status akun berhasil diubah menjadi ${newStatus}`,
          "success"
        );

        setTimeout(() => location.reload(), 1500);
      } else {
        showNotification(data.message || "Gagal mengubah status akun", "error");

        if (alpineComponent) alpineComponent.loading = false;
      }
    } catch (error) {
      console.error("Error:", error);

      showNotification(
        '{{ "Terjadi kesalahan saat mengubah status akun" if current_lang == "id" else "An error occurred while changing account status" }}',
        "error"
      );

      if (alpineComponent) alpineComponent.loading = false;
    }
  };

  /* =========================
   * Notification Helper
   * ========================= */
  function showNotification(message, type = "info") {
    // Jika sudah ada global notifier (misalnya dari log_activity.js)
    if (typeof window.showNotification === "function") {
      window.showNotification(message, type);
      return;
    }

    const notification = document.createElement("div");
    notification.className = `fixed bottom-6 right-6 z-50 px-6 py-4 rounded-2xl shadow-xl border ${
      type === "success"
        ? "bg-green-600 text-white border-green-500"
        : type === "error"
        ? "bg-red-600 text-white border-red-500"
        : type === "warning"
        ? "bg-yellow-500 text-gray-900 border-yellow-400"
        : "bg-gray-800 text-white border-gray-700"
    }`;

    notification.innerHTML = `
      <div class="flex items-center gap-3">
        <i class="fa-solid ${
          type === "success"
            ? "fa-circle-check"
            : type === "error"
            ? "fa-triangle-exclamation"
            : type === "warning"
            ? "fa-exclamation-circle"
            : "fa-info-circle"
        } text-lg"></i>
        <div>
          <strong>${
            type === "success"
              ? '{{ "Berhasil" if current_lang == "id" else "Success" }}'
              : type === "error"
              ? '{{ "Error" if current_lang == "id" else "Error" }}'
              : '{{ "Info" if current_lang == "id" else "Info" }}'
          }</strong><br>
          <span class="text-sm">${message}</span>
        </div>
      </div>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.style.transition = "opacity 0.3s";
      notification.style.opacity = "0";
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }

  // Expose fallback notifier jika belum ada
  if (typeof window.showNotification === "undefined") {
    window.showNotification = showNotification;
  }
});

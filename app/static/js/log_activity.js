document.addEventListener("DOMContentLoaded", () => {
  const csrfMeta = document.querySelector('meta[name="csrf-token"]');
  const csrfToken = csrfMeta ? csrfMeta.content : null;

  /* =========================
   * Toast Notification
   * ========================= */
  window.showNotification = function (message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast flex items-center gap-3 px-6 py-4 rounded-lg shadow-lg min-w-[300px] max-w-md ${
      type === "success"
        ? "bg-green-500 text-white"
        : type === "error"
        ? "bg-red-500 text-white"
        : type === "warning"
        ? "bg-yellow-500 text-gray-900"
        : "bg-blue-500 text-white"
    }`;

    const icon =
      type === "success"
        ? '<i class="fas fa-check-circle text-xl"></i>'
        : type === "error"
        ? '<i class="fas fa-times-circle text-xl"></i>'
        : type === "warning"
        ? '<i class="fas fa-exclamation-triangle text-xl"></i>'
        : '<i class="fas fa-info-circle text-xl"></i>';

    toast.innerHTML = `
      ${icon}
      <span class="flex-1 font-medium">${message}</span>
      <button class="hover:text-gray-200 transition cursor-pointer">
        <i class="fas fa-times"></i>
      </button>
    `;

    toast.querySelector("button").addEventListener("click", () => {
      toast.classList.add("hide");
      setTimeout(() => toast.remove(), 300);
    });

    container.appendChild(toast);

    setTimeout(() => {
      toast.classList.add("hide");
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  };

  /* =========================
   * Confirm Dialog
   * ========================= */
  window.showConfirmDialog = function (message, title = null) {
    return new Promise((resolve) => {
      const dialog = document.getElementById("confirm-dialog");
      if (!dialog) return resolve(false);

      const titleEl = document.getElementById("confirm-title");
      const messageEl = document.getElementById("confirm-message");
      const cancelBtn = document.getElementById("confirm-cancel");
      const okBtn = document.getElementById("confirm-ok");

      titleEl.textContent =
        title ??
        '{{ "Konfirmasi" if current_lang == "id" else "Confirmation" }}';
      messageEl.textContent = message;

      dialog.classList.remove("hidden");
      dialog.classList.add("flex");

      const newCancel = cancelBtn.cloneNode(true);
      const newOk = okBtn.cloneNode(true);
      cancelBtn.replaceWith(newCancel);
      okBtn.replaceWith(newOk);

      const close = (result) => {
        dialog.classList.add("hide");
        setTimeout(() => {
          dialog.classList.remove("flex", "hide");
          dialog.classList.add("hidden");
          resolve(result);
        }, 200);
      };

      newCancel.addEventListener("click", () => close(false));
      newOk.addEventListener("click", () => close(true));

      dialog.addEventListener("click", (e) => {
        if (e.target === dialog) close(false);
      });

      const escHandler = (e) => {
        if (e.key === "Escape") {
          close(false);
          document.removeEventListener("keydown", escHandler);
        }
      };
      document.addEventListener("keydown", escHandler);
    });
  };

  /* =========================
   * Show Log Detail
   * ========================= */
  window.showLogDetail = async function (logId) {
    try {
      const res = await fetch(`/api/log_aktivitas/detail/${logId}`, {
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
      });

      const data = await res.json();
      if (!data.success) {
        showNotification(data.message || "Gagal memuat detail log", "error");
        return;
      }

      const log = data.log;
      const content = document.getElementById("log-detail-content");

      const isDark =
        document.documentElement.classList.contains("dark") ||
        (window.Alpine && Alpine.store("theme")?.isDark);

      const textColor = isDark ? "text-gray-400" : "text-gray-600";

      content.innerHTML = `
        <div class="space-y-3">
          <div><label class="text-sm font-semibold ${textColor}">{{ "User" if current_lang == "id" else "User" }}:</label><p>${
        log.user_name || "-"
      }</p></div>
          <div><label class="text-sm font-semibold ${textColor}">{{ "Role" if current_lang == "id" else "Role" }}:</label><p>${
        log.user_role || "-"
      }</p></div>
          <div><label class="text-sm font-semibold ${textColor}">{{ "Aktivitas" if current_lang == "id" else "Activity" }}:</label><p>${
        log.aktivitas || "-"
      }</p></div>
          <div><label class="text-sm font-semibold ${textColor}">IP:</label><p>${
        log.ip_address || "-"
      }</p></div>
          <div><label class="text-sm font-semibold ${textColor}">{{ "User Agent" if current_lang == "id" else "User Agent" }}:</label><p class="break-all">${
        log.user_agent || "-"
      }</p></div>
          <div><label class="text-sm font-semibold ${textColor}">{{ "Tanggal & Waktu" if current_lang == "id" else "Date & Time" }}:</label><p>${
        log.timestamp || "-"
      }</p></div>
        </div>
      `;

      const modal = document.getElementById("log-detail-modal");
      modal.classList.remove("hidden");
      modal.classList.add("flex");
    } catch (err) {
      console.error(err);
      showNotification("Terjadi kesalahan", "error");
    }
  };

  /* =========================
   * Close Log Detail
   * ========================= */
  window.closeLogDetail = function () {
    const modal = document.getElementById("log-detail-modal");
    if (!modal) return;

    modal.classList.add("hide");
    setTimeout(() => {
      modal.classList.remove("flex", "hide");
      modal.classList.add("hidden");
    }, 200);
  };

  /* =========================
   * Delete Log
   * ========================= */
  window.deleteLog = async function (logId) {
    const confirmed = await showConfirmDialog(
      '{{ "Apakah Anda yakin ingin menghapus log aktivitas ini?" if current_lang == "id" else "Are you sure you want to delete this activity log?" }}'
    );

    if (!confirmed) return;

    try {
      const res = await fetch(`/api/log_aktivitas/delete/${logId}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
      });

      const data = await res.json();
      if (data.success) {
        showNotification(data.message, "success");
        setTimeout(() => location.reload(), 1000);
      } else {
        showNotification(data.message, "error");
      }
    } catch (err) {
      console.error(err);
      showNotification("Terjadi kesalahan", "error");
    }
  };

  /* =========================
   * Export Logs
   * ========================= */
  window.exportLogs = function (format) {
    const params = new URLSearchParams(window.location.search);
    params.set("export", format);
    window.location.href = `/admin/log_aktivitas/export?${params.toString()}`;
  };

  /* =========================
   * Modal Backdrop Click
   * ========================= */
  document
    .getElementById("log-detail-modal")
    ?.addEventListener("click", (e) => {
      if (e.target.id === "log-detail-modal") {
        closeLogDetail();
      }
    });
});

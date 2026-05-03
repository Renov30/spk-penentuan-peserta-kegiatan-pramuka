// Ambil CSRF token dari meta tag
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;

// ================================
// Toast Notification Function
// ================================
function showNotification(message, type = "info") {
  const container = document.getElementById("toast-container");
  if (!container) {
    console.error("Toast container not found");
    return;
  }

  // Create toast element
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

  // Icon based on type
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
    <button onclick="this.parentElement.classList.add('hide'); setTimeout(() => this.parentElement.remove(), 300)"
            class="text-white hover:text-gray-200 transition cursor-pointer">
      <i class="fas fa-times"></i>
    </button>
  `;

  container.appendChild(toast);

  // Auto remove after 4 seconds
  setTimeout(() => {
    toast.classList.add("hide");
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ================================
// Custom Confirm Dialog Function
// ================================
function showConfirmDialog(message, title = null) {
  return new Promise((resolve) => {
    const dialog = document.getElementById("confirm-dialog");
    const titleEl = document.getElementById("confirm-title");
    const messageEl = document.getElementById("confirm-message");
    const cancelBtn = document.getElementById("confirm-cancel");
    const okBtn = document.getElementById("confirm-ok");

    // Set content
    if (title) {
      titleEl.textContent = title;
    } else {
      titleEl.textContent =
        '{{ "Konfirmasi" if current_lang == "id" else "Confirmation" }}';
    }
    messageEl.textContent = message;

    // Show dialog
    dialog.classList.remove("hidden");
    dialog.classList.add("flex");

    // Remove previous event listeners by cloning
    const newCancelBtn = cancelBtn.cloneNode(true);
    const newOkBtn = okBtn.cloneNode(true);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
    okBtn.parentNode.replaceChild(newOkBtn, okBtn);

    // Close function
    const closeDialog = (result) => {
      dialog.classList.add("hide");
      setTimeout(() => {
        dialog.classList.remove("flex", "hide");
        dialog.classList.add("hidden");
        resolve(result);
      }, 200);
    };

    // Event listeners
    newCancelBtn.addEventListener("click", () => closeDialog(false));
    newOkBtn.addEventListener("click", () => closeDialog(true));

    // Close on backdrop click
    dialog.addEventListener("click", (e) => {
      if (e.target === dialog) {
        closeDialog(false);
      }
    });

    // Close on Escape key
    const escapeHandler = (e) => {
      if (e.key === "Escape") {
        closeDialog(false);
        document.removeEventListener("keydown", escapeHandler);
      }
    };
    document.addEventListener("keydown", escapeHandler);
  });
}

// ================================
// Mark Notification as Read
// ================================
function markAsRead(notificationId) {
  fetch(`/api/notifikasi/mark-read/${notificationId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        const notificationEl = document.getElementById(
          `notification-${notificationId}`
        );
        if (notificationEl) {
          notificationEl.classList.remove("border-blue-500");
          notificationEl.classList.add("border-gray-300");

          const bellIcon = notificationEl.querySelector("i.fa-bell");
          if (bellIcon) {
            bellIcon.classList.remove("text-blue-500");
            bellIcon.classList.add("text-gray-400");
          }

          const markReadBtn = notificationEl.querySelector(
            'button[onclick*="markAsRead"]'
          );
          if (markReadBtn) markReadBtn.remove();

          const newBadge = notificationEl.querySelector("span.bg-blue-500");
          if (newBadge) newBadge.remove();

          notificationEl.setAttribute("data-status", "read");

          const statusFilter = document.getElementById("filterStatus");
          if (statusFilter && statusFilter.value === "unread") {
            notificationEl.style.display = "none";
            filterNotifications();
          }
        }
        showNotification(
          data.message || "Notifikasi ditandai sebagai dibaca",
          "success"
        );
      } else {
        showNotification(data.message || "Gagal menandai notifikasi", "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Terjadi kesalahan", "error");
    });
}

// ================================
// Mark All Notifications as Read
// ================================
async function markAllAsRead() {
  const confirmed = await showConfirmDialog(
    '{{ "Apakah Anda yakin ingin menandai semua notifikasi sebagai dibaca?" if current_lang == "id" else "Are you sure you want to mark all notifications as read?" }}'
  );

  if (!confirmed) return;

  fetch("/api/notifikasi/mark-all-read", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        showNotification(
          data.message || "Semua notifikasi ditandai sebagai dibaca",
          "success"
        );
        setTimeout(() => location.reload(), 1000);
      } else {
        showNotification(
          data.message || "Gagal menandai semua notifikasi",
          "error"
        );
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Terjadi kesalahan", "error");
    });
}

// ================================
// Delete Notification
// ================================
async function deleteNotification(notificationId) {
  const confirmed = await showConfirmDialog(
    '{{ "Apakah Anda yakin ingin menghapus notifikasi ini?" if current_lang == "id" else "Are you sure you want to delete this notification?" }}'
  );

  if (!confirmed) return;

  fetch(`/api/notifikasi/delete/${notificationId}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.success) {
        const notificationEl = document.getElementById(
          `notification-${notificationId}`
        );
        if (notificationEl) {
          notificationEl.style.transition = "opacity 0.3s";
          notificationEl.style.opacity = "0";
          setTimeout(() => {
            notificationEl.remove();
            const notificationsList =
              document.getElementById("notificationsList");
            if (notificationsList && notificationsList.children.length === 0) {
              notificationsList.innerHTML = `
                <div class="rounded-xl shadow p-12 text-center {{ 'bg-gray-900 text-white' if current_theme == 'dark' else 'bg-white text-black' }}">
                  <i class="fa-solid fa-bell-slash text-6xl text-gray-400 mb-4"></i>
                  <p class="text-lg {{ 'text-gray-300' if current_theme == 'dark' else 'text-gray-600' }}">
                    {{ 'Tidak ada notifikasi' if current_lang == 'id' else 'No notifications' }}
                  </p>
                </div>
              `;
            }
          }, 300);
        }
        showNotification(
          data.message || "Notifikasi berhasil dihapus",
          "success"
        );
      } else {
        showNotification(data.message || "Gagal menghapus notifikasi", "error");
      }
    })
    .catch((error) => {
      console.error("Error:", error);
      showNotification("Terjadi kesalahan", "error");
    });
}

// ================================
// Filter and Search Notifications
// ================================
function filterNotifications() {
  const searchInput = document.getElementById("searchNotification");
  const categoryFilter = document.getElementById("filterCategory");
  const statusFilter = document.getElementById("filterStatus");

  if (!searchInput || !categoryFilter || !statusFilter) return;

  const searchTerm = (searchInput.value || "").toLowerCase();
  const selectedCategory = categoryFilter.value;
  const selectedStatus = statusFilter.value;

  const notificationItems = document.querySelectorAll(".notification-item");
  let visibleCount = 0;

  notificationItems.forEach((item) => {
    const category = item.getAttribute("data-category");
    const status = item.getAttribute("data-status");
    const message = item.getAttribute("data-message") || "";

    const matchesSearch = searchTerm === "" || message.includes(searchTerm);
    const matchesCategory =
      selectedCategory === "all" || category === selectedCategory;
    const matchesStatus = selectedStatus === "all" || status === selectedStatus;

    if (matchesSearch && matchesCategory && matchesStatus) {
      item.style.display = "flex";
      visibleCount++;
    } else {
      item.style.display = "none";
    }
  });

  // No results message
  const notificationsList = document.getElementById("notificationsList");
  let noResultsMsg = notificationsList.querySelector(".no-results-message");

  if (visibleCount === 0 && notificationItems.length > 0) {
    if (!noResultsMsg) {
      noResultsMsg = document.createElement("div");
      noResultsMsg.className = `no-results-message rounded-xl shadow p-12 text-center {{ 'bg-gray-900 text-white' if current_theme == 'dark' else 'bg-white text-black' }}`;
      noResultsMsg.innerHTML = `
        <i class="fa-solid fa-search text-6xl text-gray-400 mb-4"></i>
        <p class="text-lg {{ 'text-gray-300' if current_theme == 'dark' else 'text-gray-600' }}">
          {{ 'Tidak ada notifikasi yang sesuai dengan filter' if current_lang == 'id' else 'No notifications match the filter' }}
        </p>
      `;
      notificationsList.appendChild(noResultsMsg);
    }
  } else {
    if (noResultsMsg) noResultsMsg.remove();
  }
}

// ================================
// Initialize filter on page load
// ================================
document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("searchNotification");
  const categoryFilter = document.getElementById("filterCategory");
  const statusFilter = document.getElementById("filterStatus");

  if (searchInput && categoryFilter && statusFilter) {
    if (
      searchInput.value ||
      categoryFilter.value !== "all" ||
      statusFilter.value !== "all"
    ) {
      filterNotifications();
    }
  }
});

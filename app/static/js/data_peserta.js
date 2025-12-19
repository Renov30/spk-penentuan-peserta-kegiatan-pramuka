// Data Peserta Management JavaScript
document.addEventListener("DOMContentLoaded", function () {
  let allPeserta = [];
  let filteredPeserta = [];
  let kegiatanFilter = null;
  let searchInput = null;
  let statusFilter = null;

  // Get CSRF token
  const csrfToken =
    document
      .querySelector('meta[name="csrf-token"]')
      ?.getAttribute("content") || "";

  // Initialize DOM elements
  searchInput =
    document.querySelector("#searchInput") ||
    document.querySelector(
      'input[placeholder*="Cari peserta"], input[placeholder*="Search participants"]'
    );

  kegiatanFilter = document.querySelector("#kegiatanFilter");

  statusFilter =
    document.querySelector("#statusFilter") ||
    document.querySelector("select:not(#kegiatanFilter)");

  // Setup event listeners
  if (searchInput) {
    searchInput.addEventListener("input", function (e) {
      filterPeserta();
    });
  }

  if (kegiatanFilter) {
    kegiatanFilter.addEventListener("change", function (e) {
      loadPesertaData(); // Reload data when kegiatan filter changes
    });
  }

  if (statusFilter) {
    statusFilter.addEventListener("change", function (e) {
      filterPeserta();
    });
  }

  // Initialize - load data after DOM is ready
  setTimeout(() => {
    loadPesertaData();
    loadStatistics();
  }, 100);

  // Load peserta data from API
  function loadPesertaData() {
    // Show loading state
    const tbody = document.querySelector("table tbody");
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" class="px-4 py-8 text-center text-gray-500">
            <i class="fa-solid fa-spinner fa-spin mr-2"></i>
            Memuat data...
          </td>
        </tr>
      `;
    }

    // Get kegiatan filter value - re-query if needed
    const kegiatanFilterEl = document.querySelector("#kegiatanFilter");
    const kegiatanId =
      kegiatanFilterEl && kegiatanFilterEl.value ? kegiatanFilterEl.value : "";
    const url = kegiatanId
      ? `/api/peserta/list?kegiatan_id=${kegiatanId}`
      : "/api/peserta/list";

    console.log("Fetching data from:", url);

    fetch(url, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "same-origin", // Include cookies for session
    })
      .then((response) => {
        console.log("Response status:", response.status);
        console.log("Response headers:", response.headers);

        // Check if response is ok
        if (!response.ok) {
          // Try to get error message from response
          return response.text().then((text) => {
            console.error("Response error:", text);
            throw new Error(`HTTP error! status: ${response.status}`);
          });
        }

        // Check content type
        const contentType = response.headers.get("content-type");
        if (!contentType || !contentType.includes("application/json")) {
          return response.text().then((text) => {
            console.error("Response is not JSON:", text.substring(0, 200));
            throw new Error("Response is not JSON");
          });
        }

        return response.json();
      })
      .then((data) => {
        console.log("Received data:", data);

        // Handle response - check if peserta exists (can be empty array)
        if (data && data.success !== undefined) {
          allPeserta = Array.isArray(data.peserta) ? data.peserta : [];
          filteredPeserta = [...allPeserta];
          console.log(`Loaded ${allPeserta.length} peserta`);

          if (allPeserta.length === 0) {
            console.log("No peserta found");
          }

          renderTable();
        } else {
          console.error(
            "Error loading peserta:",
            data?.message || "Unknown error"
          );
          const errorMsg = data?.message || "Gagal memuat data peserta";

          if (tbody) {
            tbody.innerHTML = `
              <tr>
                <td colspan="7" class="px-4 py-8 text-center text-red-500">
                <i class="fa-solid fa-exclamation-triangle mr-2"></i>
                ${escapeHtml(errorMsg)}
              </td>
              </tr>
            `;
          }
          showNotification(errorMsg, "error");
        }
      })
      .catch((error) => {
        console.error("Fetch error:", error);

        if (tbody) {
          tbody.innerHTML = `
            <tr>
              <td colspan="7" class="px-4 py-8 text-center text-red-500">
                <i class="fa-solid fa-exclamation-triangle mr-2"></i>
                Terjadi kesalahan saat memuat data. Silakan refresh halaman atau hubungi administrator.
                <br><small class="text-gray-400 mt-2 block">${escapeHtml(
                  error.message || "Unknown error"
                )}</small>
              </td>
            </tr>
          `;
        }
        showNotification(
          "Terjadi kesalahan saat memuat data: " +
            (error.message || "Unknown error"),
          "error"
        );
      });
  }

  // Filter peserta based on search and status
  function filterPeserta() {
    // Re-query elements in case they weren't found initially
    const searchInputEl = searchInput || document.querySelector("#searchInput");
    const statusFilterEl =
      statusFilter || document.querySelector("#statusFilter");

    const searchTerm = searchInputEl ? searchInputEl.value.toLowerCase() : "";
    const statusFilterValue = statusFilterEl ? statusFilterEl.value : "";

    filteredPeserta = allPeserta.filter((peserta) => {
      const matchesSearch =
        !searchTerm ||
        peserta.nama_lengkap.toLowerCase().includes(searchTerm) ||
        peserta.email.toLowerCase().includes(searchTerm) ||
        (peserta.asal_gudep &&
          peserta.asal_gudep.toLowerCase().includes(searchTerm));

      const matchesStatus =
        !statusFilterValue ||
        statusFilterValue === "Semua Status" ||
        statusFilterValue === "All Status" ||
        peserta.status === statusFilterValue.toLowerCase();

      return matchesSearch && matchesStatus;
    });

    renderTable();
  }

  // Render table with peserta data
  function renderTable() {
    const tbody = document.querySelector("table tbody");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (filteredPeserta.length === 0) {
      tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="px-4 py-8 text-center text-gray-500">
                        Tidak ada data peserta
                    </td>
                </tr>
            `;
      return;
    }

    filteredPeserta.forEach((peserta, index) => {
      const row = document.createElement("tr");
      // CSS will handle hover effect with dark mode
      row.className = "border-b";

      // Get status badge
      const statusBadge = getStatusBadge(peserta.status);

      // Get score (if available)
      const score = peserta.skor_akhir ? peserta.skor_akhir.toFixed(2) : "-";

      // Get kegiatan names
      let kegiatanNames = "-";
      if (
        peserta.registered_activities &&
        peserta.registered_activities.length > 0
      ) {
        kegiatanNames = peserta.registered_activities
          .map((act) => escapeHtml(act.nama || ""))
          .filter((n) => n)
          .join(", ");
        if (kegiatanNames.length > 50) {
          kegiatanNames = kegiatanNames.substring(0, 50) + "...";
        }
      }

      row.innerHTML = `
                <td class="px-4 py-3">${index + 1}</td>
                <td class="px-4 py-3">${escapeHtml(
                  peserta.nama_lengkap || "-"
                )}</td>
                <td class="px-4 py-3">${escapeHtml(
                  peserta.asal_gudep || "-"
                )}</td>
                <td class="px-4 py-3" title="${
                  peserta.registered_activities &&
                  peserta.registered_activities.length > 0
                    ? peserta.registered_activities
                        .map((a) => a.nama)
                        .join(", ")
                    : ""
                }">${kegiatanNames}</td>
                <td class="px-4 py-3">${statusBadge}</td>
                <td class="px-4 py-3">${score}</td>
                <td class="px-4 py-3 flex gap-2">
                    <button 
                        onclick="viewPeserta(${peserta.user_id})"
                        class="px-3 py-1 bg-gray-400 text-white rounded-lg hover:bg-gray-500 flex items-center cursor-pointer"
                        aria-label="Lihat Detail"
                    >
                        <i class="fa-solid fa-eye"></i>
                    </button>
                    <button 
                        onclick="editPeserta(${peserta.user_id})"
                        class="px-3 py-1 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center cursor-pointer"
                        aria-label="Edit"
                    >
                        <i class="fa-solid fa-pen-to-square"></i>
                    </button>
                    <button 
                        onclick="deletePeserta(${
                          peserta.user_id
                        }, '${escapeHtml(peserta.nama_lengkap)}')"
                        class="px-3 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600 flex items-center cursor-pointer"
                        aria-label="Hapus"
                    >
                        <i class="fa-solid fa-trash"></i>
                    </button>
                    <button 
                        onclick="printKartuPeserta(${peserta.user_id})"
                        class="px-3 py-1 bg-purple-500 text-white rounded-lg hover:bg-purple-600 flex items-center cursor-pointer"
                        aria-label="Cetak Kartu Peserta"
                    >
                        <i class="fa-solid fa-id-card"></i>
                    </button>
                    <button 
                        onclick="tambahPesertaKegiatan(${peserta.user_id}, ${
        peserta.participant_id || "null"
      })"
                        class="px-3 py-1 bg-orange-500 text-white rounded-lg hover:bg-orange-600 flex items-center cursor-pointer"
                        aria-label="Tambah ke Kegiatan"
                        title="Tambah ke Kegiatan"
                    >
                        <i class="fa-solid fa-calendar-plus"></i>
                    </button>
                </td>
            `;

      tbody.appendChild(row);
    });
  }

  // Get status badge HTML
  function getStatusBadge(status) {
    const statusText =
      status === "aktif"
        ? "Aktif"
        : status === "non-aktif"
        ? "Non-Aktif"
        : "Menunggu Verifikasi";

    const badgeClass =
      status === "aktif"
        ? "bg-green-200 text-green-800"
        : status === "non-aktif"
        ? "bg-red-200 text-red-800"
        : "bg-yellow-200 text-yellow-800";

    return `<span class="px-3 py-1 text-xs rounded-full ${badgeClass}">${statusText}</span>`;
  }

  // Load statistics for charts
  function loadStatistics() {
    fetch("/api/peserta/statistics")
      .then((response) => response.json())
      .then((data) => {
        if (data.success && data.statistics) {
          renderCharts(data.statistics);
        }
      })
      .catch((error) => {
        console.error("Error loading statistics:", error);
      });
  }

  // Render charts
  function renderCharts(stats) {
    // Status distribution chart
    renderStatusChart(stats.status);

    // Average score display
    renderAverageScore(stats.average_score);
  }

  // Render status distribution chart (simple text-based for now)
  function renderStatusChart(statusData) {
    const chartContainer = document.getElementById("chart-status");
    if (!chartContainer) return;

    const total = statusData.total || 0;
    const aktif = statusData.aktif || 0;
    const nonaktif = statusData.nonaktif || 0;

    if (total === 0) {
      chartContainer.innerHTML = '<p class="text-gray-400">Tidak ada data</p>';
      return;
    }

    const aktifPercent = ((aktif / total) * 100).toFixed(1);
    const nonaktifPercent = ((nonaktif / total) * 100).toFixed(1);

    chartContainer.innerHTML = `
            <div class="w-full space-y-2">
                <div class="flex items-center justify-between">
                    <span class="text-sm">Aktif</span>
                    <span class="text-sm font-bold">${aktif} (${aktifPercent}%)</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-green-500 h-2 rounded-full" style="width: ${aktifPercent}%"></div>
                </div>
                <div class="flex items-center justify-between">
                    <span class="text-sm">Non-Aktif</span>
                    <span class="text-sm font-bold">${nonaktif} (${nonaktifPercent}%)</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-red-500 h-2 rounded-full" style="width: ${nonaktifPercent}%"></div>
                </div>
            </div>
        `;
  }

  // Render average score
  function renderAverageScore(avgScore) {
    const chartContainer = document.getElementById("chart-score");
    if (!chartContainer) return;

    chartContainer.innerHTML = `
            <div class="text-center">
                <div class="text-4xl font-bold ${
                  avgScore >= 70
                    ? "text-green-600"
                    : avgScore >= 50
                    ? "text-yellow-600"
                    : "text-red-600"
                }">
                    ${avgScore.toFixed(2)}
                </div>
                <p class="text-sm text-gray-500 mt-2">Rata-rata Skor</p>
            </div>
        `;
  }

  // View peserta detail
  window.viewPeserta = function (userId) {
    fetch(`/api/peserta/detail/${userId}`)
      .then((response) => response.json())
      .then((data) => {
        if (data.success && data.peserta) {
          showPesertaModal(data.peserta);
        } else {
          showNotification("Gagal memuat detail peserta", "error");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        showNotification("Terjadi kesalahan", "error");
      });
  };

  // Edit peserta
  window.editPeserta = function (userId) {
    // Redirect to edit page or open modal
    window.location.href = `/admin/users?edit=${userId}`;
  };

  // Delete peserta
  window.deletePeserta = function (userId, nama) {
    if (!confirm(`Apakah Anda yakin ingin menghapus peserta "${nama}"?`)) {
      return;
    }

    const formData = new FormData();
    formData.append("csrf_token", csrfToken);

    fetch(`/api/peserta/delete/${userId}`, {
      method: "POST",
      body: formData,
      headers: {
        "X-CSRFToken": csrfToken,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showNotification("Peserta berhasil dihapus", "success");
          loadPesertaData();
          loadStatistics();
        } else {
          showNotification(data.message || "Gagal menghapus peserta", "error");
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        showNotification("Terjadi kesalahan saat menghapus", "error");
      });
  };

  // Print kartu peserta
  window.printKartuPeserta = function (userId) {
    // Open kartu peserta page in new window
    window.open(`/admin/peserta/kartu/${userId}`, "_blank");
  };

  // Tambah peserta ke kegiatan
  window.tambahPesertaKegiatan = function (userId, participantId) {
    // Redirect ke halaman tambah peserta ke kegiatan dengan user_id
    const url = participantId
      ? `/admin/peserta/tambah-kegiatan?user_id=${userId}&participant_id=${participantId}`
      : `/admin/peserta/tambah-kegiatan?user_id=${userId}`;
    window.location.href = url;
  };

  // Show peserta detail modal
  function showPesertaModal(peserta) {
    const modal = document.createElement("div");
    modal.className =
      "fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50";
    modal.innerHTML = `
            <div class="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                <div class="flex justify-between items-center mb-4">
                    <h2 class="text-2xl font-bold">Detail Peserta</h2>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700">
                        <i class="fa-solid fa-times"></i>
                    </button>
                </div>
                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <div>
                            <label class="text-sm font-semibold text-gray-600">Nama Lengkap</label>
                            <p class="mt-1">${escapeHtml(
                              peserta.nama_lengkap || "-"
                            )}</p>
                        </div>
                        <div>
                            <label class="text-sm font-semibold text-gray-600">Email</label>
                            <p class="mt-1">${escapeHtml(
                              peserta.email || "-"
                            )}</p>
                        </div>
                        <div>
                            <label class="text-sm font-semibold text-gray-600">Jenis Kelamin</label>
                            <p class="mt-1">${escapeHtml(
                              peserta.jenis_kelamin || "-"
                            )}</p>
                        </div>
                        <div>
                            <label class="text-sm font-semibold text-gray-600">Usia</label>
                            <p class="mt-1">${escapeHtml(
                              peserta.usia || "-"
                            )}</p>
                        </div>
                        <div>
                            <label class="text-sm font-semibold text-gray-600">Nomor HP</label>
                            <p class="mt-1">${escapeHtml(
                              peserta.nomor_hp || "-"
                            )}</p>
                        </div>
                        <div>
                            <label class="text-sm font-semibold text-gray-600">Status</label>
                            <div class="mt-1">${getStatusBadge(
                              peserta.status
                            )}</div>
                        </div>
                        <div>
                            <label class="text-sm font-semibold text-gray-600">Golongan</label>
                            <p class="mt-1">${escapeHtml(
                              peserta.golongan || "-"
                            )}</p>
                        </div>
                        <div>
                            <label class="text-sm font-semibold text-gray-600">Tingkatan</label>
                            <p class="mt-1">${escapeHtml(
                              peserta.tingkatan || "-"
                            )}</p>
                        </div>
                        <div>
                            <label class="text-sm font-semibold text-gray-600">Asal Gudep</label>
                            <p class="mt-1">${escapeHtml(
                              peserta.asal_gudep || "-"
                            )}</p>
                        </div>
                        <div>
                            <label class="text-sm font-semibold text-gray-600">Asal Kwarran</label>
                            <p class="mt-1">${escapeHtml(
                              peserta.asal_kwarran || "-"
                            )}</p>
                        </div>
                        <div>
                            <label class="text-sm font-semibold text-gray-600">Asal Kwarcab</label>
                            <p class="mt-1">${escapeHtml(
                              peserta.asal_kwarcab || "-"
                            )}</p>
                        </div>
                        <div>
                            <label class="text-sm font-semibold text-gray-600">Asal Kwarda</label>
                            <p class="mt-1">${escapeHtml(
                              peserta.asal_kwarda || "-"
                            )}</p>
                        </div>
                    </div>
                    ${
                      peserta.registered_activities &&
                      peserta.registered_activities.length > 0
                        ? `
                        <div class="mt-4">
                            <label class="text-sm font-semibold text-gray-600">Kegiatan Terdaftar</label>
                            <ul class="mt-2 space-y-2">
                                ${peserta.registered_activities
                                  .map(
                                    (activity) => `
                                    <li class="p-2 bg-gray-100 dark:bg-gray-700 rounded">
                                        <strong>${escapeHtml(
                                          activity.nama
                                        )}</strong> - ${escapeHtml(
                                      activity.jenis
                                    )}
                                        ${
                                          activity.skor
                                            ? `<br><span class="text-sm">Skor: ${activity.skor.toFixed(
                                                2
                                              )} | Ranking: ${
                                                activity.ranking || "-"
                                              }</span>`
                                            : ""
                                        }
                                    </li>
                                `
                                  )
                                  .join("")}
                            </ul>
                        </div>
                    `
                        : ""
                    }
                </div>
                <div class="mt-6 flex justify-end gap-2">
                    <button onclick="this.closest('.fixed').remove()" class="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600">
                        Tutup
                    </button>
                </div>
            </div>
        `;
    document.body.appendChild(modal);
  }

  // Utility functions
  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function showNotification(message, type = "info") {
    // You can integrate with your existing notification system
    alert(message);
  }

  // Export functionality
  const exportBtn = document.querySelector("button:has(.fa-file-export)");
  if (exportBtn) {
    exportBtn.addEventListener("click", function () {
      exportToExcel();
    });
  }

  // Import functionality
  const importBtn = document.querySelector("button:has(.fa-file-import)");
  if (importBtn) {
    importBtn.addEventListener("click", function () {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = ".xlsx,.xls,.csv";
      input.onchange = function (e) {
        const file = e.target.files[0];
        if (file) {
          importFromExcel(file);
        }
      };
      input.click();
    });
  }

  // Export to Excel
  function exportToExcel() {
    // Create CSV content
    const headers = [
      "No",
      "Nama Lengkap",
      "Email",
      "Jenis Kelamin",
      "Usia",
      "Asal Gudep",
      "Status",
    ];
    const rows = filteredPeserta.map((p, index) => [
      index + 1,
      p.nama_lengkap || "",
      p.email || "",
      p.jenis_kelamin || "",
      p.usia || "",
      p.asal_gudep || "",
      p.status || "",
    ]);

    const csvContent = [
      headers.join(","),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(",")),
    ].join("\n");

    const blob = new Blob(["\ufeff" + csvContent], {
      type: "text/csv;charset=utf-8;",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `data_peserta_${
      new Date().toISOString().split("T")[0]
    }.csv`;
    link.click();
  }

  // Import from Excel
  function importFromExcel(file) {
    showNotification("Fitur import sedang dalam pengembangan", "info");
  }

  // Add peserta button
  const addBtn = document.querySelector("button:has(.fa-user-plus)");
  if (addBtn) {
    addBtn.addEventListener("click", function () {
      window.location.href = "/admin/add_user?level=peserta";
    });
  }
});

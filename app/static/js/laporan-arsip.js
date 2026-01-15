function laporanArsipData() {
  return {
    arsipList: Array.isArray(window.INIT_ARSIP) ? window.INIT_ARSIP : [],
    filteredArsip: [],
    searchQuery: "",
    filterType: "",
    selectedEventId: "",
    generateEventId: "",
    showGenerateModal: false,
    isDeleting: false,

    init() {
      this.filteredArsip = [...this.arsipList];
    },

    filterArsip() {
      let data = [...this.arsipList];

      if (this.selectedEventId) {
        data = data.filter((a) => a.event_id == this.selectedEventId);
      }

      if (this.filterType) {
        data = data.filter((a) => a.file_type === this.filterType);
      }

      if (this.searchQuery) {
        const q = this.searchQuery.toLowerCase();
        data = data.filter(
          (a) =>
            (a.nama_arsip || "").toLowerCase().includes(q) ||
            (a.nama_kegiatan || "").toLowerCase().includes(q)
        );
      }

      this.filteredArsip = data;
    },

    async generateReport(type) {
      if (!this.generateEventId) {
        const message =
          this.current_lang === "id"
            ? "Silakan pilih kegiatan terlebih dahulu sebelum membuat laporan."
            : "Please select an event before generating the report.";

        this.showAlert("warning", message);
        return;
      }

      const endpoint =
        type === "excel"
          ? `/api/generate_laporan_excel/${this.generateEventId}`
          : `/api/generate_laporan_pdf/${this.generateEventId}`;

      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: {
            "X-CSRFToken": window.CSRF_TOKEN,
          },
        });

        const data = await res.json();

        if (data.success) {
          this.showAlert("success", data.message);
          setTimeout(() => window.location.reload(), 1500);
        } else {
          this.showAlert("error", data.message || "Gagal membuat laporan");
        }
      } catch (err) {
        console.error(err);
        this.showAlert("error", "Terjadi kesalahan pada server");
      }
    },

    viewArsip(arsip) {
      if (!arsip || !arsip.id) return;

      window.open(`/api/view_arsip/${arsip.id}`, "_blank");
    },

    async downloadArsip(arsipId) {
      window.location.href = `/api/download_arsip/${arsipId}`;
    },

    async deleteArsipConfirmed() {
      if (!this.confirmDelete.id) return;

      this.isDeleting = true;

      try {
        const res = await fetch(`/api/hapus_arsip/${this.confirmDelete.id}`, {
          method: "DELETE",
          headers: {
            "X-CSRFToken": window.CSRF_TOKEN,
          },
        });

        const data = await res.json();

        if (!res.ok || !data.success) {
          throw new Error(data.message || "Delete failed");
        }

        this.arsipList = this.arsipList.filter(
          (a) => a.id !== this.confirmDelete.id
        );
        this.filterArsip();

        this.showAlert(
          "success",
          this.current_lang === "id"
            ? "Arsip berhasil dihapus."
            : "Archive successfully deleted."
        );
      } catch (err) {
        console.error(err);
        this.showAlert(
          "error",
          this.current_lang === "id"
            ? "Gagal menghapus arsip."
            : "Failed to delete archive."
        );
      } finally {
        this.isDeleting = false;
        this.closeDeleteModal();
      }
    },

    alert: {
      show: false,
      type: "info",
      message: "",
    },

    alertTimeout: null,

    showAlert(type, message, timeout = 3000) {
      this.alert.type = type;
      this.alert.message = message;
      this.alert.show = true;

      if (this.alertTimeout) clearTimeout(this.alertTimeout);

      if (timeout) {
        this.alertTimeout = setTimeout(() => {
          this.alert.show = false;
        }, timeout);
      }
    },

    confirmDelete: {
      show: false,
      id: null,
    },

    openDeleteModal(id) {
      this.confirmDelete.id = id;
      this.confirmDelete.show = true;
    },

    closeDeleteModal() {
      this.confirmDelete.show = false;
      this.confirmDelete.id = null;
    },
  };
}

async function saveConfig() {
  const comp = document.getElementById("configComponent");
  if (!comp) {
    console.error("configComponent not found");
    return;
  }
  const state = Alpine.$data(comp);
  const bodyState = Alpine.$data(document.body);

  // ✅ validasi semua activities + criteria di dalamnya
  for (let act of state.activities || []) {
    if (!act.nama || !act.mulai || !act.selesai) {
      bodyState.modal = {
        show: true,
        title: "Peringatan",
        message: "Nama kegiatan dan periode wajib diisi",
      };
      return;
    }

    // Validasi: Periode Seleksi harus selesai sebelum Waktu Pelaksanaan dimulai
    if (act.waktuMulai) {
      const waktuMulai = new Date(act.waktuMulai);

      // Cek apakah mulai periode seleksi >= waktu pelaksanaan
      if (act.mulai) {
        const mulai = new Date(act.mulai);
        if (mulai >= waktuMulai) {
          bodyState.modal = {
            show: true,
            title: "Peringatan",
            message: `Periode Seleksi (mulai) untuk kegiatan "${
              act.nama || "ini"
            }" harus sebelum Waktu Pelaksanaan dimulai`,
          };
          return;
        }
      }

      // Cek apakah selesai periode seleksi >= waktu pelaksanaan
      if (act.selesai) {
        const selesai = new Date(act.selesai);
        if (selesai >= waktuMulai) {
          bodyState.modal = {
            show: true,
            title: "Peringatan",
            message: `Periode Seleksi (selesai) untuk kegiatan "${
              act.nama || "ini"
            }" harus sebelum Waktu Pelaksanaan dimulai`,
          };
          return;
        }
      }
    }

    // Validasi: Waktu Pelaksanaan tidak boleh dalam kurun waktu Periode Seleksi
    if (act.mulai && act.selesai) {
      const mulai = new Date(act.mulai);
      const selesai = new Date(act.selesai);

      // Cek apakah waktu pelaksanaan mulai dalam periode seleksi
      if (act.waktuMulai) {
        const waktuMulai = new Date(act.waktuMulai);
        if (waktuMulai >= mulai && waktuMulai <= selesai) {
          bodyState.modal = {
            show: true,
            title: "Peringatan",
            message: `Waktu Pelaksanaan (mulai) untuk kegiatan "${
              act.nama || "ini"
            }" tidak boleh dalam kurun waktu Periode Seleksi`,
          };
          return;
        }
      }

      // Cek apakah waktu pelaksanaan selesai dalam periode seleksi
      if (act.waktuSelesai) {
        const waktuSelesai = new Date(act.waktuSelesai);
        if (waktuSelesai >= mulai && waktuSelesai <= selesai) {
          bodyState.modal = {
            show: true,
            title: "Peringatan",
            message: `Waktu Pelaksanaan (selesai) untuk kegiatan "${
              act.nama || "ini"
            }" tidak boleh dalam kurun waktu Periode Seleksi`,
          };
          return;
        }
      }

      // Cek apakah waktu pelaksanaan overlap dengan periode seleksi (waktu pelaksanaan mencakup seluruh periode seleksi)
      if (act.waktuMulai && act.waktuSelesai) {
        const waktuMulai = new Date(act.waktuMulai);
        const waktuSelesai = new Date(act.waktuSelesai);
        if (waktuMulai <= mulai && waktuSelesai >= selesai) {
          bodyState.modal = {
            show: true,
            title: "Peringatan",
            message: `Waktu Pelaksanaan untuk kegiatan "${
              act.nama || "ini"
            }" tidak boleh mencakup seluruh Periode Seleksi`,
          };
          return;
        }
      }
    }

    for (let c of act.criteria || []) {
      if (!c.nama) {
        bodyState.modal = {
          show: true,
          title: "Peringatan",
          message: "Semua kriteria wajib diisi namanya",
        };
        return;
      }
      if (!c.skala || c.skala < 1 || c.skala > 10) {
        bodyState.modal = {
          show: true,
          title: "Peringatan",
          message: "Skala kriteria harus bernilai 1–10",
        };
        return;
      }
      if (
        c.jenis === undefined ||
        c.jenis === null ||
        (Array.isArray(c.jenis) && c.jenis.length === 0) ||
        (typeof c.jenis === "string" && c.jenis.trim() === "")
      ) {
        bodyState.modal = {
          show: true,
          title: "Peringatan",
          message: "Jenis penilaian wajib diatur",
        };
        return;
      }
    }
  }

  // Sinkronkan data contingents ke activities (jumlahkan semua umpi)
  for (let i = 0; i < state.activities.length; i++) {
    if (state.contingents[i] && Array.isArray(state.contingents[i])) {
      // Jumlahkan semua umpi untuk activity ini
      const totalPutra = state.contingents[i].reduce((sum, umpi) => sum + (umpi.umpiPutra || 0), 0);
      const totalPutri = state.contingents[i].reduce((sum, umpi) => sum + (umpi.umpiPutri || 0), 0);
      state.activities[i].putra = totalPutra;
      state.activities[i].putri = totalPutri;
    } else if (state.contingents[i]) {
      // Backward compatibility: jika masih format lama
      state.activities[i].putra = state.contingents[i].umpiPutra || 0;
      state.activities[i].putri = state.contingents[i].umpiPutri || 0;
    }
  }

  // Siapkan payload dengan activities (yang sudah berisi putra/putri) dan criteria
  const payload = {
    activities: state.activities,
  };

  // CSRF token
  const csrfTokenEl = document.querySelector('meta[name="csrf-token"]');
  const csrfToken = csrfTokenEl ? csrfTokenEl.content : "";

  try {
    const res = await fetch("/api/save_config", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(payload),
    });
    const text = await res.text();
    let result;
    try {
      result = JSON.parse(text);
    } catch (err) {
      throw new Error("Invalid JSON response: " + text);
    }
    if (result.status === "success") {
      bodyState.modal = {
        show: true,
        title: "Berhasil",
        message: result.message,
      };
      setTimeout(() => {
        bodyState.page = "main";
      }, 1000);
    } else {
      bodyState.modal = {
        show: true,
        title: "Error",
        message: result.message || "Terjadi kesalahan",
      };
    }
  } catch (err) {
    console.error("saveConfig error", err);
    bodyState.modal = {
      show: true,
      title: "Error",
      message: err.message || "Terjadi kesalahan pada server.",
    };
  }
}

// Function Save Periode
function savePeriode() {
  const comp = document.getElementById("configComponent");
  if (!comp) return;
  const state = Alpine.$data(comp);
  const invalidAct = state.activities.find(
    (a) => !a.nama || !a.mulai || !a.selesai
  );
  if (invalidAct) {
    state.errorMessage = "Nama kegiatan dan periode harus diisi";
    return;
  }

  // Validasi: Periode Seleksi harus selesai sebelum Waktu Pelaksanaan dimulai
  for (let act of state.activities) {
    if (act.waktuMulai) {
      const waktuMulai = new Date(act.waktuMulai);

      // Cek apakah mulai periode seleksi >= waktu pelaksanaan
      if (act.mulai) {
        const mulai = new Date(act.mulai);
        if (mulai >= waktuMulai) {
          state.errorMessage =
            "Periode Seleksi (mulai) harus sebelum Waktu Pelaksanaan dimulai";
          return;
        }
      }

      // Cek apakah selesai periode seleksi >= waktu pelaksanaan
      if (act.selesai) {
        const selesai = new Date(act.selesai);
        if (selesai >= waktuMulai) {
          state.errorMessage =
            "Periode Seleksi (selesai) harus sebelum Waktu Pelaksanaan dimulai";
          return;
        }
      }
    }
  }

  // Validasi: Waktu Pelaksanaan tidak boleh dalam kurun waktu Periode Seleksi
  for (let act of state.activities) {
    if (act.mulai && act.selesai) {
      const mulai = new Date(act.mulai);
      const selesai = new Date(act.selesai);

      // Cek apakah waktu pelaksanaan mulai dalam periode seleksi
      if (act.waktuMulai) {
        const waktuMulai = new Date(act.waktuMulai);
        if (waktuMulai >= mulai && waktuMulai <= selesai) {
          state.errorMessage =
            "Waktu Pelaksanaan (mulai) tidak boleh dalam kurun waktu Periode Seleksi";
          return;
        }
      }

      // Cek apakah waktu pelaksanaan selesai dalam periode seleksi
      if (act.waktuSelesai) {
        const waktuSelesai = new Date(act.waktuSelesai);
        if (waktuSelesai >= mulai && waktuSelesai <= selesai) {
          state.errorMessage =
            "Waktu Pelaksanaan (selesai) tidak boleh dalam kurun waktu Periode Seleksi";
          return;
        }
      }

      // Cek apakah waktu pelaksanaan overlap dengan periode seleksi (waktu pelaksanaan mencakup seluruh periode seleksi)
      if (act.waktuMulai && act.waktuSelesai) {
        const waktuMulai = new Date(act.waktuMulai);
        const waktuSelesai = new Date(act.waktuSelesai);
        if (waktuMulai <= mulai && waktuSelesai >= selesai) {
          state.errorMessage =
            "Waktu Pelaksanaan tidak boleh mencakup seluruh Periode Seleksi";
          return;
        }
      }
    }
  }

  // ✅ Sinkronisasi array contingents agar sama panjang dengan activities
  if (state.contingents.length !== state.activities.length) {
    state.contingents = state.activities.map((act, i) => {
      return (
        state.contingents[i] || {
          nama: act.nama,
          umpiPutra: 0,
          umpiPutri: 0,
        }
      );
    });
  }

  // set completed & tab
  state.completed.periode = true;
  state.tab = "kuota";
  state.errorMessage = "";
}

// Function Push Kriteria Default
function getDefaultCriteria() {
  return [
    { nama: "Status Keaktifan di Gugus Depan", skala: 1, jenis: "Kualitatif" },
    { nama: "Pencapaian SKU", skala: 1, jenis: "Kualitatif" },
    { nama: "Pencapaian SPG", skala: 1, jenis: "Kualitatif" },
    { nama: "Kesehatan Jasmani dan Rohani", skala: 1, jenis: "Kualitatif" },
    { nama: "Tes Wawancara", skala: 1, jenis: "Kualitatif" },
    {
      nama: "Tes Pilihan Ganda",
      skala: 1,
      jenis: "Kuantitatif",
      jumlahSoal: 0,
    },
  ];
}

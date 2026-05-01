document.addEventListener("DOMContentLoaded", () => {
  const dataEl = document.getElementById("tambah-peserta-data");
  if (!dataEl) return;

  const appData = JSON.parse(dataEl.textContent);

  const csrfToken = appData.csrfToken || "";
  const kegiatanInfo = appData.kegiatanInfo || {};
  const messages = appData.messages || {};

  const kegiatanSelect = document.getElementById("kegiatan_id");
  const infoDiv = document.getElementById("infoKegiatan");
  const detailsDiv = document.getElementById("kegiatanDetails");
  const form = document.getElementById("formTambahPeserta");
  const submitBtn = document.getElementById("submitBtn");

  // =============================
  // Update info kegiatan
  // =============================
  kegiatanSelect?.addEventListener("change", function () {
    const kegiatanId = this.value;

    if (kegiatanId && kegiatanInfo[kegiatanId]) {
      const k = kegiatanInfo[kegiatanId];
      detailsDiv.innerHTML = `
        <p><strong>Nama Kegiatan:</strong> ${k.nama}</p>
        <p><strong>Jenis:</strong> ${k.jenis}</p>
        <p><strong>Tempat:</strong> ${k.tempat}</p>
        <p><strong>Waktu:</strong> ${k.mulai} - ${k.selesai}</p>
      `;
      infoDiv.classList.remove("hidden");
    } else {
      infoDiv.classList.add("hidden");
    }
  });

  // =============================
  // Submit form
  // =============================
  window.submitForm = function () {
    const kegiatanId = kegiatanSelect.value;
    const checkboxes = document.querySelectorAll(
      'input[name="participant_ids[]"]:checked'
    );

    if (!kegiatanId) {
      alert(messages.selectActivity);
      return;
    }

    if (checkboxes.length === 0) {
      alert(messages.selectParticipant);
      return;
    }

    submitBtn.disabled = true;
    submitBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i>${messages.processing}`;

    const participantIds = [];

    checkboxes.forEach((cb) => {
      const hasBiodata = cb.dataset.hasBiodata === "true";
      if (hasBiodata) {
        participantIds.push(parseInt(cb.value));
      } else {
        const userId = parseInt(cb.dataset.userId);
        if (!isNaN(userId)) participantIds.push(userId);
      }
    });

    fetch("/api/peserta/tambah-kegiatan-bulk", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify({
        kegiatan_id: parseInt(kegiatanId),
        participant_ids: participantIds,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          alert(data.message || messages.success);
          form.reset();
          document
            .querySelectorAll('input[type="checkbox"]')
            .forEach((cb) => (cb.checked = false));
          infoDiv.classList.add("hidden");
        } else {
          alert(data.message || messages.failed);
        }
      })
      .catch((err) => {
        console.error(err);
        alert(messages.failed);
      })
      .finally(() => {
        submitBtn.disabled = false;
        submitBtn.innerHTML =
          '<i class="fa-solid fa-plus mr-2"></i>Tambah Peserta ke Kegiatan';
      });
  };
});

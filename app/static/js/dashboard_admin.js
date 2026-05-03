document.addEventListener("DOMContentLoaded", function () {
  /* ===============================
     THEME CONFIG
  =============================== */
  const isDark = window.IS_DARK_THEME === true;
  const textColor = isDark ? "#ffffff" : "#000000";
  const gridColor = isDark ? "rgba(255, 255, 255, 0.1)" : "rgba(0, 0, 0, 0.1)";

  if (typeof Chart === "undefined") {
    console.error("Chart.js belum dimuat");
    return;
  }

  Chart.defaults.color = textColor;
  Chart.defaults.borderColor = gridColor;

  /* ===============================
     FETCH DASHBOARD DATA
  =============================== */
  fetch("/api/admin/dashboard/charts")
    .then((response) => response.json())
    .then((res) => {
      if (!res.success) return;

      const d = res.data;
      const L = window.DASHBOARD_LABELS || {};

      /* ===============================
         CHART 1 — USER DISTRIBUTION
      =============================== */
      const userDist = document.getElementById("userDistributionChart");
      if (userDist) {
        new Chart(userDist, {
          type: "pie",
          data: {
            labels: L.user_roles,
            datasets: [
              {
                data: [
                  d.user_distribution.admin,
                  d.user_distribution.penilai,
                  d.user_distribution.peserta,
                ],
                backgroundColor: [
                  "rgba(59,130,246,.8)",
                  "rgba(16,185,129,.8)",
                  "rgba(139,92,246,.8)",
                ],
                borderWidth: 2,
              },
            ],
          },
          options: chartLegendOptions(),
        });
      }

      /* ===============================
         CHART 2 — STATUS PESERTA
      =============================== */
      const pesertaStatus = document.getElementById("pesertaStatusChart");
      if (pesertaStatus) {
        new Chart(pesertaStatus, {
          type: "doughnut",
          data: {
            labels: L.peserta_status,
            datasets: [
              {
                data: [d.peserta_status.aktif, d.peserta_status.nonaktif],
                backgroundColor: ["rgba(16,185,129,.8)", "rgba(239,68,68,.8)"],
                borderWidth: 2,
              },
            ],
          },
          options: chartLegendOptions(),
        });
      }

      /* ===============================
         CHART 3 — GENDER
      =============================== */
      const gender = document.getElementById("pesertaGenderChart");
      if (gender) {
        new Chart(gender, {
          type: "bar",
          data: {
            labels: L.gender,
            datasets: [
              {
                label: L.count,
                data: [d.peserta_gender.laki_laki, d.peserta_gender.perempuan],
                backgroundColor: ["rgba(59,130,246,.8)", "rgba(236,72,153,.8)"],
                borderWidth: 2,
              },
            ],
          },
          options: barOptions(),
        });
      }

      /* ===============================
         CHART 4 — NOTIFICATIONS
      =============================== */
      const notif = document.getElementById("notificationStatusChart");
      if (notif) {
        new Chart(notif, {
          type: "pie",
          data: {
            labels: L.notification_status,
            datasets: [
              {
                data: [d.notifications.read, d.notifications.unread],
                backgroundColor: ["rgba(16,185,129,.8)", "rgba(245,158,11,.8)"],
                borderWidth: 2,
              },
            ],
          },
          options: chartLegendOptions(),
        });
      }

      /* ===============================
         CHART 5 — EVENT STATISTICS
      =============================== */
      const events = document.getElementById("eventStatisticsChart");
      if (events) {
        new Chart(events, {
          type: "bar",
          data: {
            labels: L.events,
            datasets: [
              {
                label: L.event_count,
                data: [
                  d.events.total,
                  d.events.aktif,
                  d.events.selesai,
                  d.events.mendatang,
                ],
                backgroundColor: [
                  "rgba(59,130,246,.8)",
                  "rgba(16,185,129,.8)",
                  "rgba(107,114,128,.8)",
                  "rgba(245,158,11,.8)",
                ],
                borderWidth: 2,
              },
            ],
          },
          options: barOptions(),
        });
      }

      /* ===============================
         CHART 6 — DATA SUMMARY
      =============================== */
      const summary = document.getElementById("dataSummaryChart");
      if (summary) {
        new Chart(summary, {
          type: "bar",
          data: {
            labels: L.summary,
            datasets: [
              {
                label: L.total,
                data: window.DASHBOARD_TOTALS,
                backgroundColor: "rgba(139,92,246,.8)",
                borderWidth: 2,
              },
            ],
          },
          options: barOptions(true),
        });
      }
    })
    .catch((err) => {
      console.error("Error loading chart data:", err);
    });

  /* ===============================
     HELPERS
  =============================== */
  function chartLegendOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "bottom",
          labels: { color: textColor, font: { size: 11 } },
        },
      },
    };
  }

  function barOptions(rotateX = false) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { color: textColor, font: { size: 10 } },
          grid: { color: gridColor },
        },
        x: {
          ticks: {
            color: textColor,
            font: { size: 9 },
            maxRotation: rotateX ? 45 : 0,
            minRotation: rotateX ? 45 : 0,
          },
          grid: { color: gridColor },
        },
      },
    };
  }
});

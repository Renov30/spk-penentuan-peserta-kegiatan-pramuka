/**
 * Settings Page Script
 * - Toast Notification
 * - Alpine.js Settings Page
 */

/* =========================
 * Toast Notification
 * ========================= */
function showNotification(message, type = "info") {
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

  toast.innerHTML = `
    <span class="flex-1 font-medium">${message}</span>
    <button onclick="this.parentElement.remove()">✕</button>
  `;

  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

window.showNotification = showNotification;

/* =========================
 * Alpine Settings Page
 * ========================= */
document.addEventListener("alpine:init", () => {
  Alpine.data("settingsPage", () => ({
    activeTab: "email",

    emailSettings: {
      ...window.APP_SETTINGS.emailSettings,
      mail_use_tls: window.APP_SETTINGS.emailSettings.mail_use_tls === "true",
      mail_use_ssl: window.APP_SETTINGS.emailSettings.mail_use_ssl === "true",
      mail_enabled: window.APP_SETTINGS.emailSettings.mail_enabled === "true",
      mail_password: "",
    },

    smsSettings: {
      ...window.APP_SETTINGS.smsSettings,
      sms_enabled: window.APP_SETTINGS.smsSettings.sms_enabled === "true",
      twilio_auth_token: "",
    },

    appSettings: window.APP_SETTINGS.appSettings,

    logoPath: window.APP_SETTINGS.appSettings.logo_path,
    logoFile: null,

    handleLogoUpload(e) {
      this.logoFile = e.target.files[0];
    },

    async uploadLogo() {
      if (!this.logoFile) {
        showNotification(APP_SETTINGS.texts.logo_required, "warning");
        return;
      }

      const formData = new FormData();
      formData.append("logo", this.logoFile);

      try {
        const res = await fetch("/api/upload_logo", {
          method: "POST",
          headers: { "X-CSRFToken": APP_SETTINGS.csrfToken },
          body: formData,
        });

        const json = await res.json();

        if (json.status === "success") {
          this.logoPath = json.logo_path;
          showNotification(APP_SETTINGS.texts.logo_success, "success");
        } else {
          showNotification(APP_SETTINGS.texts.logo_failed, "error");
        }
      } catch {
        showNotification(APP_SETTINGS.texts.error_generic, "error");
      }
    },

    async saveSettings(category) {
      let payload = { category };

      if (category === "email") {
        payload = {
          ...payload,
          ...this.emailSettings,
          mail_use_tls: this.emailSettings.mail_use_tls ? "true" : "false",
          mail_use_ssl: this.emailSettings.mail_use_ssl ? "true" : "false",
          mail_enabled: this.emailSettings.mail_enabled ? "true" : "false",
        };
      }

      if (category === "sms") {
        payload = {
          ...payload,
          ...this.smsSettings,
          sms_enabled: this.smsSettings.sms_enabled ? "true" : "false",
        };
      }

      if (category === "app") {
        payload = { ...payload, ...this.appSettings };
      }

      try {
        const res = await fetch("/api/save_settings", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": APP_SETTINGS.csrfToken,
          },
          body: JSON.stringify(payload),
        });

        const json = await res.json();
        showNotification(
          json.status === "success"
            ? APP_SETTINGS.texts.save_success
            : APP_SETTINGS.texts.save_failed,
          json.status === "success" ? "success" : "error"
        );
      } catch {
        showNotification(APP_SETTINGS.texts.error_generic, "error");
      }
    },

    async testEmail() {
      const email = prompt(
        APP_SETTINGS.texts.test_email_prompt,
        APP_SETTINGS.texts.test_email_default
      );
      if (!email) return;

      try {
        const res = await fetch("/api/test_email", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": APP_SETTINGS.csrfToken,
          },
          body: JSON.stringify({ email }),
        });

        const json = await res.json();
        showNotification(json.message, json.status);
      } catch {
        showNotification(APP_SETTINGS.texts.error_generic, "error");
      }
    },
  }));
});

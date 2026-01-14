function assignmentManager() {
  return {
    assignments: window.INIT_ASSIGNMENTS,
    eventsCriteria: window.INIT_EVENTS_CRITERIA,

    // Modal state
    showModal: false,
    currentEvaluatorId: null,
    currentEventId: null,
    currentEvaluatorName: "",
    currentEventName: "",
    currentEventCriteria: [],
    selectedCriteria: [],

    hasAssignment(evaluatorId, eventId) {
      return (
        this.assignments[evaluatorId] &&
        this.assignments[evaluatorId][eventId] &&
        this.assignments[evaluatorId][eventId].length > 0
      );
    },

    getAssignmentLabel(evaluatorId, eventId) {
      if (!this.hasAssignment(evaluatorId, eventId)) {
        return window.LABEL_ASSIGN;
      }
      const count = this.assignments[evaluatorId][eventId].length;
      const total = this.eventsCriteria[eventId]
        ? this.eventsCriteria[eventId].length
        : 0;

      if (total === 0) return "N/A";
      return count === total ? "All" : `${count}/${total}`;
    },

    getAssignmentCount(evaluatorId, eventId) {
      if (!this.hasAssignment(evaluatorId, eventId)) return 0;
      return this.assignments[evaluatorId][eventId].length;
    },

    openModal(evaluatorId, eventId, evaluatorName, eventName) {
      this.currentEvaluatorId = evaluatorId;
      this.currentEventId = eventId;
      this.currentEvaluatorName = evaluatorName;
      this.currentEventName = eventName;
      this.currentEventCriteria = this.eventsCriteria[eventId] || [];

      if (
        this.assignments[evaluatorId] &&
        this.assignments[evaluatorId][eventId]
      ) {
        this.selectedCriteria = [...this.assignments[evaluatorId][eventId]];
      } else {
        this.selectedCriteria = [];
      }

      this.showModal = true;
    },

    closeModal() {
      this.showModal = false;
      this.selectedCriteria = [];
    },

    toggleAll(checked) {
      if (checked) {
        this.selectedCriteria = this.currentEventCriteria.map((c) => c.id);
      } else {
        this.selectedCriteria = [];
      }
    },

    async saveAssignment() {
      const url = "/api/update_evaluator_criteria";
      const csrfToken = document
        .querySelector('meta[name="csrf-token"]')
        .getAttribute("content");

      try {
        const response = await fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify({
            evaluator_id: this.currentEvaluatorId,
            event_id: this.currentEventId,
            criteria_ids: this.selectedCriteria,
          }),
        });

        const data = await response.json();

        if (data.status === "success") {
          if (!this.assignments[this.currentEvaluatorId]) {
            this.assignments[this.currentEvaluatorId] = {};
          }

          this.assignments[this.currentEvaluatorId][this.currentEventId] = [
            ...this.selectedCriteria,
          ];

          showNotification(data.message, "success");
          this.closeModal();

          setTimeout(() => location.reload(), 1000);
        } else {
          showNotification(data.message, "error");
        }
      } catch (error) {
        console.error("Error:", error);
        showNotification(window.LABEL_ERROR, "error");
      }
    },
  };
}

function showNotification(message, type) {
  const container = document.getElementById("toast-container");

  const toast = document.createElement("div");
  toast.className = `toast flex items-center gap-3 px-6 py-4 rounded-lg shadow-lg min-w-[300px] max-w-md ${
    type === "success"
      ? "bg-green-500 text-white"
      : type === "error"
      ? "bg-red-500 text-white"
      : "bg-blue-500 text-white"
  }`;

  const icon =
    type === "success"
      ? '<i class="fas fa-check-circle text-xl"></i>'
      : type === "error"
      ? '<i class="fas fa-times-circle text-xl"></i>'
      : '<i class="fas fa-info-circle text-xl"></i>';

  toast.innerHTML = `
    ${icon}
    <span class="flex-1 font-medium">${message}</span>
    <button onclick="this.parentElement.remove()" class="text-white hover:text-gray-200">
      <i class="fas fa-times"></i>
    </button>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("hide");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

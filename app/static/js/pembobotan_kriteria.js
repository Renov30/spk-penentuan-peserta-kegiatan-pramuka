function pembobotanData() {
  const DATA = window.PEMBOBOTAN_DATA;

  return {
    ready: false,

    selectedEventId: DATA.selectedEventId,
    criteriaList: DATA.criteriaList || [],
    pairwiseMatrix: DATA.pairwiseMatrix || [],
    ahpResults: DATA.ahpResults,
    weights: {},

    init() {
      this.initializeMatrix();
      this.loadWeights();
      this.ready = true;
    },

    loadWeights() {
      if (this.ahpResults && this.ahpResults.weights_json) {
        try {
          this.weights = JSON.parse(this.ahpResults.weights_json);
        } catch (e) {
          console.error("Error parsing weights:", e);
        }
      }
    },

    initializeMatrix() {
      if (this.criteriaList.length > 0 && this.pairwiseMatrix.length === 0) {
        const n = this.criteriaList.length;
        this.pairwiseMatrix = Array.from({ length: n }, () => Array(n).fill(1));
      }
    },

    loadEventData() {
      if (!this.selectedEventId) return;
      window.location.href = `/admin/pembobotan_kriteria?event_id=${this.selectedEventId}`;
    },

    updateReciprocal(i, j) {
      if (i === j) {
        this.pairwiseMatrix[i][j] = 1;
        return;
      }

      const value = parseFloat(this.pairwiseMatrix[i][j]);
      if (value > 0) {
        this.pairwiseMatrix[j][i] = +(1 / value).toFixed(3);
      }
    },

    async saveMatrix() {
      if (!this.selectedEventId) {
        alert(DATA.texts.select_event);
        return;
      }

      try {
        const response = await fetch(
          `/api/save_pairwise_matrix/${this.selectedEventId}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": DATA.csrfToken,
            },
            body: JSON.stringify({
              matrix: this.pairwiseMatrix,
            }),
          }
        );

        const result = await response.json();

        if (result.success) {
          alert(result.message);
          this.loadEventData();
        } else {
          alert(result.message);
        }
      } catch (error) {
        console.error(error);
        alert(DATA.texts.save_error);
      }
    },

    async calculateAHP(useFuzzy = false) {
      if (!this.selectedEventId) {
        alert(DATA.texts.select_event);
        return;
      }

      try {
        const response = await fetch(
          `/api/calculate_ahp/${this.selectedEventId}`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              "X-CSRFToken": DATA.csrfToken,
            },
            body: JSON.stringify({
              use_fuzzy: useFuzzy,
            }),
          }
        );

        const result = await response.json();

        if (result.success) {
          alert(result.message);
          this.loadEventData();
        } else {
          alert(result.message);
        }
      } catch (error) {
        console.error(error);
        alert(DATA.texts.calc_error);
      }
    },
  };
}

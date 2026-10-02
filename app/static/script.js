
document.addEventListener("DOMContentLoaded", function () {

    const chartCanvas = document.getElementById("telemetryChart");

    if (chartCanvas) {
        const labels = JSON.parse(
            chartCanvas.dataset.labels
        );

        const anomalies = JSON.parse(
            chartCanvas.dataset.anomalies
        );

        if (typeof Chart !== "undefined") {
            new Chart(chartCanvas, {
                type: "line",

                data: {
                    labels: labels,

                    datasets: [{
                        label: "Anomaly Detection",
                        data: anomalies,
                        borderColor: "#57d6f5",
                        backgroundColor: "rgba(87, 214, 245, 0.15)",
                        pointRadius: anomalies.map(
                            value => value === 1 ? 5 : 2
                        ),
                        pointBackgroundColor: anomalies.map(
                            value => value === 1 ? "#ff727c" : "#57d6f5"
                        ),
                        tension: 0.2,
                        fill: true
                    }]
                },

                options: {
                    responsive: true,

                    plugins: {
                        legend: {
                            labels: {
                                color: "#e8eef8"
                            }
                        }
                    },

                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: "Observation",
                                color: "#91a0b8"
                            },
                            ticks: {
                                color: "#91a0b8"
                            },
                            grid: {
                                color: "#263550"
                            }
                        },

                        y: {
                            min: 0,
                            max: 1,
                            ticks: {
                                stepSize: 1,
                                color: "#91a0b8"
                            },
                            grid: {
                                color: "#263550"
                            }
                        }
                    }
                }
            });
        }
    }

    document.querySelectorAll('input[type="file"]').forEach(input => {
        input.addEventListener("change", function () {
            if (this.files.length > 0) {
                console.log("Selected file:", this.files[0].name);
            }
        });
    });

});
"use strict";

document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("telemetryForm");
    const fileInput = document.getElementById("telemetryFile");
    const dropZone = document.getElementById("dropZone");
    const selectedFile = document.getElementById("selectedFile");
    const fileName = document.getElementById("fileName");
    const fileSize = document.getElementById("fileSize");
    const removeFile = document.getElementById("removeFile");
    const analyzeButton = document.getElementById("analyzeButton");
    const analyzeButtonText = document.getElementById("analyzeButtonText");

    if (!form || !fileInput || !dropZone) {
        return;
    }

    function formatFileSize(bytes) {
        if (!Number.isFinite(bytes) || bytes <= 0) {
            return "0 KB";
        }

        if (bytes < 1024) {
            return bytes + " Bytes";
        }

        if (bytes < 1024 * 1024) {
            return (bytes / 1024).toFixed(2) + " KB";
        }

        return (bytes / (1024 * 1024)).toFixed(2) + " MB";
    }

    function isValidFile(file) {
        if (!file || !file.name) {
            return false;
        }

        const name = file.name.toLowerCase();

        return (
            name.endsWith(".csv") ||
            name.endsWith(".xlsx") ||
            name.endsWith(".xls")
        );
    }

    function showFile(file) {
        if (!file || !isValidFile(file)) {
            alert("Please select a CSV, XLSX, or XLS telemetry file.");
            return false;
        }

        /*
         * IMPORTANT:
         * Keep the real File object inside the actual
         * <input type="file"> element so Flask receives it.
         */
        try {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
        } catch (error) {
            console.error("Could not attach file to input:", error);
            return false;
        }

        if (!fileInput.files || fileInput.files.length === 0) {
            return false;
        }

        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        selectedFile.hidden = false;

        return true;
    }

    function clearFile() {
        fileInput.value = "";

        selectedFile.hidden = true;
        fileName.textContent = "filename.csv";
        fileSize.textContent = "0 KB";
    }

    /*
     * Normal file selection.
     */
    fileInput.addEventListener("change", function () {
        const file = fileInput.files[0];

        if (!file) {
            return;
        }

        if (!isValidFile(file)) {
            clearFile();
            alert("Please select a CSV, XLSX, or XLS telemetry file.");
            return;
        }

        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        selectedFile.hidden = false;
    });

    /*
     * Dragging a file over the upload area.
     */
    ["dragenter", "dragover"].forEach(function (eventName) {
        dropZone.addEventListener(eventName, function (event) {
            event.preventDefault();
            event.stopPropagation();

            dropZone.classList.add("dragover");
        });
    });

    /*
     * Leaving or dropping on the upload area.
     */
    ["dragleave", "drop"].forEach(function (eventName) {
        dropZone.addEventListener(eventName, function (event) {
            event.preventDefault();
            event.stopPropagation();

            dropZone.classList.remove("dragover");
        });
    });

    /*
     * Actual drag-and-drop handling.
     */
    dropZone.addEventListener("drop", function (event) {
        const files = event.dataTransfer.files;

        if (!files || files.length === 0) {
            return;
        }

        showFile(files[0]);
    });

    /*
     * Remove selected file.
     */
    if (removeFile) {
        removeFile.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();

            clearFile();
        });
    }

    /*
     * IMPORTANT:
     * Before the form is sent, make absolutely sure that
     * the browser has a real file attached to the input.
     */
    form.addEventListener("submit", function (event) {
        if (!fileInput.files || fileInput.files.length === 0) {
            event.preventDefault();

            alert("Please select a telemetry CSV file before starting analysis.");

            return;
        }

        const file = fileInput.files[0];

        if (!isValidFile(file)) {
            event.preventDefault();

            alert("Please select a valid CSV, XLSX, or XLS telemetry file.");

            return;
        }

        if (analyzeButton) {
            analyzeButton.disabled = true;
        }

        if (analyzeButtonText) {
            analyzeButtonText.textContent = "Analyzing telemetry...";
        }
    });

    /*
     * Plotly results chart.
     */
    const chartElement = document.getElementById("telemetryChart");

    if (
        chartElement &&
        typeof Plotly !== "undefined"
    ) {
        const chartData = chartElement.dataset.chart;

        if (chartData) {
            try {
                const parsedChart = JSON.parse(chartData);

                if (
                    parsedChart &&
                    Array.isArray(parsedChart.data)
                ) {
                    Plotly.newPlot(
                        chartElement,
                        parsedChart.data,
                        parsedChart.layout || {},
                        {
                            responsive: true,
                            displaylogo: false,
                            modeBarButtonsToRemove: [
                                "lasso2d",
                                "select2d"
                            ]
                        }
                    );
                }
            } catch (error) {
                console.error(
                    "Unable to render telemetry chart:",
                    error
                );
            }
        }
    }
});
/**
 * AERIS - Image analysis frontend
 *
 * Handles image upload validation, drag-and-drop interaction,
 * preview generation, and upload feedback.
 */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    initializeImageUpload();
    initializeImageForm();
});


const ALLOWED_IMAGE_EXTENSIONS = new Set([
    "jpg",
    "jpeg",
    "png",
    "bmp",
    "tif",
    "tiff",
    "webp",
]);


const MAX_PREVIEW_SIZE = 5 * 1024 * 1024;


/**
 * Initialize image drag-and-drop and file selection.
 */
function initializeImageUpload() {
    const uploadArea = document.querySelector(
        "[data-image-upload]"
    );

    const fileInput = document.querySelector(
        'input[type="file"][accept*="image"]'
    );

    if (!uploadArea || !fileInput) {
        return;
    }

    uploadArea.addEventListener("click", (event) => {
        if (event.target === fileInput) {
            return;
        }

        fileInput.click();
    });

    uploadArea.addEventListener("dragover", (event) => {
        event.preventDefault();
        uploadArea.classList.add("dragover");
    });

    uploadArea.addEventListener("dragleave", () => {
        uploadArea.classList.remove("dragover");
    });

    uploadArea.addEventListener("drop", (event) => {
        event.preventDefault();
        uploadArea.classList.remove("dragover");

        const files = event.dataTransfer.files;

        if (!files || files.length === 0) {
            return;
        }

        const file = files[0];

        if (!isValidImage(file)) {
            showImageMessage(
                "Please select a supported image file.",
                "error"
            );
            return;
        }

        try {
            const dataTransfer = new DataTransfer();
            dataTransfer.items.add(file);
            fileInput.files = dataTransfer.files;
        } catch (error) {
            // Some browsers prevent programmatic file assignment.
        }

        updateImageFileName(file);
        generateImagePreview(file);
    });

    fileInput.addEventListener("change", () => {
        const file = fileInput.files[0];

        if (!file) {
            return;
        }

        if (!isValidImage(file)) {
            fileInput.value = "";

            showImageMessage(
                "Unsupported image format. Please use JPG, JPEG, PNG, BMP, TIF, TIFF, or WEBP.",
                "error"
            );

            return;
        }

        updateImageFileName(file);
        generateImagePreview(file);
    });
}


/**
 * Validate an image file before upload.
 *
 * @param {File} file
 * @returns {boolean}
 */
function isValidImage(file) {
    if (!file) {
        return false;
    }

    const fileName = file.name || "";

    if (!fileName.includes(".")) {
        return false;
    }

    const extension = fileName
        .split(".")
        .pop()
        .toLowerCase();

    return ALLOWED_IMAGE_EXTENSIONS.has(extension);
}


/**
 * Update visible filename labels.
 *
 * @param {File} file
 */
function updateImageFileName(file) {
    const nameElements = document.querySelectorAll(
        "[data-image-file-name]"
    );

    nameElements.forEach((element) => {
        element.textContent = file.name;
    });
}


/**
 * Generate a local preview of the selected image.
 *
 * The preview is only generated in the browser. The actual image
 * is still uploaded to Flask for server-side analysis.
 *
 * @param {File} file
 */
function generateImagePreview(file) {
    const preview = document.querySelector(
        "[data-image-preview]"
    );

    if (!preview) {
        return;
    }

    if (file.size > MAX_PREVIEW_SIZE) {
        preview.removeAttribute("src");
        preview.hidden = true;

        showImageMessage(
            "The image is valid, but its preview is too large to display here.",
            "info"
        );

        return;
    }

    if (!window.FileReader) {
        return;
    }

    const reader = new FileReader();

    reader.onload = (event) => {
        preview.src = event.target.result;
        preview.hidden = false;
    };

    reader.onerror = () => {
        preview.removeAttribute("src");
        preview.hidden = true;

        showImageMessage(
            "The image preview could not be generated.",
            "error"
        );
    };

    reader.readAsDataURL(file);
}


/**
 * Initialize image-analysis form validation and submission feedback.
 */
function initializeImageForm() {
    const form = document.querySelector(
        'form[data-image-form]'
    );

    if (!form) {
        return;
    }

    form.addEventListener("submit", (event) => {
        const fileInput = form.querySelector(
            'input[type="file"]'
        );

        if (!fileInput || !fileInput.files.length) {
            event.preventDefault();

            showImageMessage(
                "Please select an image before starting analysis.",
                "error"
            );

            return;
        }

        const file = fileInput.files[0];

        if (!isValidImage(file)) {
            event.preventDefault();

            showImageMessage(
                "Please select a supported image file.",
                "error"
            );

            return;
        }

        const submitButton = form.querySelector(
            'button[type="submit"]'
        );

        if (submitButton) {
            submitButton.disabled = true;
            submitButton.dataset.originalText =
                submitButton.textContent;
            submitButton.textContent = "Analyzing image...";
        }

        const progress = document.querySelector(
            "[data-image-progress]"
        );

        if (progress) {
            progress.hidden = false;
        }
    });
}


/**
 * Display a temporary image-analysis message.
 *
 * @param {string} message
 * @param {string} type
 */
function showImageMessage(message, type = "info") {
    if (
        window.AERIS &&
        typeof window.AERIS.showClientMessage === "function"
    ) {
        window.AERIS.showClientMessage(
            message,
            type
        );

        return;
    }

    const container = document.querySelector(
        "[data-message-container]"
    );

    if (!container) {
        return;
    }

    const alert = document.createElement("div");

    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alert.setAttribute("role", "alert");

    container.prepend(alert);

    window.setTimeout(() => {
        alert.style.opacity = "0";
        alert.style.transition = "opacity 250ms ease";

        window.setTimeout(() => {
            alert.remove();
        }, 300);
    }, 5000);
}
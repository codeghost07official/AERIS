/**
 * AERIS - Global frontend JavaScript
 *
 * Handles small UI interactions shared across the application.
 */

"use strict";

document.addEventListener("DOMContentLoaded", () => {
    initializeFlashMessages();
    initializePasswordToggles();
    initializeConfirmations();
    initializeAutoDismissButtons();
});


/**
 * Automatically hide flash messages after a short period.
 */
function initializeFlashMessages() {
    const alerts = document.querySelectorAll(".alert");

    alerts.forEach((alert) => {
        const dismissible = alert.dataset.dismissible !== "false";

        if (!dismissible) {
            return;
        }

        window.setTimeout(() => {
            alert.style.opacity = "0";
            alert.style.transition = "opacity 250ms ease";

            window.setTimeout(() => {
                alert.remove();
            }, 300);
        }, 5000);
    });
}


/**
 * Add show/hide functionality to password fields.
 *
 * Supported markup:
 * <button data-password-toggle="passwordFieldId">
 */
function initializePasswordToggles() {
    const toggles = document.querySelectorAll(
        "[data-password-toggle]"
    );

    toggles.forEach((toggle) => {
        toggle.addEventListener("click", () => {
            const targetId = toggle.dataset.passwordToggle;

            if (!targetId) {
                return;
            }

            const input = document.getElementById(targetId);

            if (!input) {
                return;
            }

            const isPassword = input.type === "password";

            input.type = isPassword ? "text" : "password";

            toggle.setAttribute(
                "aria-label",
                isPassword ? "Hide password" : "Show password"
            );

            if (toggle.dataset.showText) {
                toggle.textContent = isPassword
                    ? toggle.dataset.hideText || "Hide"
                    : toggle.dataset.showText;
            }
        });
    });
}


/**
 * Handle confirmation dialogs for forms and buttons.
 *
 * Supported markup:
 * data-confirm="Are you sure?"
 */
function initializeConfirmations() {
    const confirmationElements = document.querySelectorAll(
        "[data-confirm]"
    );

    confirmationElements.forEach((element) => {
        element.addEventListener("click", (event) => {
            const message = element.dataset.confirm;

            if (!message) {
                return;
            }

            if (!window.confirm(message)) {
                event.preventDefault();
                event.stopPropagation();
            }
        });
    });
}


/**
 * Allow buttons to disable themselves after submission.
 *
 * Supported markup:
 * data-disable-on-submit
 */
function initializeAutoDismissButtons() {
    const forms = document.querySelectorAll(
        "form[data-disable-on-submit]"
    );

    forms.forEach((form) => {
        form.addEventListener("submit", () => {
            const submitButton = form.querySelector(
                'button[type="submit"], input[type="submit"]'
            );

            if (!submitButton) {
                return;
            }

            submitButton.disabled = true;

            const originalText =
                submitButton.dataset.originalText ||
                submitButton.textContent;

            submitButton.dataset.originalText = originalText;

            if (submitButton.tagName === "BUTTON") {
                submitButton.textContent = "Processing...";
            } else {
                submitButton.value = "Processing...";
            }
        });
    });
}


/**
 * Format a number for display in the interface.
 *
 * @param {number} value
 * @param {number} decimals
 * @returns {string}
 */
function formatNumber(value, decimals = 2) {
    const number = Number(value);

    if (!Number.isFinite(number)) {
        return "0";
    }

    return number.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
    });
}


/**
 * Safely escape text before inserting it into HTML.
 *
 * @param {string} value
 * @returns {string}
 */
function escapeHtml(value) {
    const element = document.createElement("div");
    element.textContent = String(value ?? "");
    return element.innerHTML;
}


/**
 * Display a temporary client-side message.
 *
 * @param {string} message
 * @param {string} type
 */
function showClientMessage(message, type = "info") {
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


// Make utility functions available to other AERIS scripts.
window.AERIS = {
    formatNumber,
    escapeHtml,
    showClientMessage,
};
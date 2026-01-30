// TELEMETRY PANEL LOGIC

let telemetryInterval = null;
let lastTimestamp = null;

window.startTelemetryPanel = function () {

    async function updateTelemetryPanel() {
        try {
            const t = await fetch("/telemetry/arduino/latest").then(r => r.json());

            // Only update if telemetry is NEW
            if (t.ts && t.ts === lastTimestamp) {
                return; // ignore duplicates
            }
            lastTimestamp = t.ts;

            // Update UI
            document.getElementById("rpm-value").innerText = t.rpm ?? "--";
            document.getElementById("throttle-value").innerText = t.throttle ?? "--";
            document.getElementById("direction-value").innerText = t.direction ?? "--";
            document.getElementById("voltage-value").innerText = t.voltage ?? "--";
            document.getElementById("temp-value").innerText = t.temp ?? "--";

            // Log only NEW frames
            const log = document.getElementById("telemetry-log");
            const entry = document.createElement("div");
            entry.textContent = JSON.stringify(t);
            log.prepend(entry);

        } catch (e) {
            console.error("Telemetry panel update failed", e);
        }
    }

    // Run immediately
    updateTelemetryPanel();

    // Poll every 5 seconds instead of 500ms
    telemetryInterval = setInterval(updateTelemetryPanel, 5000);
};

// ⭐ Cleanup when panel closes
window.stopTelemetryPanel = function () {
    if (telemetryInterval) {
        clearInterval(telemetryInterval);
        telemetryInterval = null;
    }
};

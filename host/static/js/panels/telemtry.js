// TELEMETRY PANEL LOGIC

async function updateTelemetryPanel() {
    try {
        const t = await fetch("/telemetry/arduino/latest").then(r => r.json());

        document.getElementById("rpm-value").innerText = t.rpm ?? "--";
        document.getElementById("throttle-value").innerText = t.throttle ?? "--";
        document.getElementById("direction-value").innerText = t.direction ?? "--";
        document.getElementById("voltage-value").innerText = t.voltage ?? "--";
        document.getElementById("temp-value").innerText = t.temp ?? "--";

        const log = document.getElementById("telemetry-log");
        const entry = document.createElement("div");
        entry.textContent = JSON.stringify(t);
        log.prepend(entry);

    } catch (e) {
        console.error("Telemetry panel update failed", e);
    }
}

setInterval(updateTelemetryPanel, 500);

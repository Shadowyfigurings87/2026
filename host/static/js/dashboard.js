async function fetchJSON(url) {
    try {
        const res = await fetch(url);
        return await res.json();
    } catch {
        return null;
    }
}

async function updateDashboard() {

    // Heartbeat
    const health = await fetchJSON("/health");
    if (health) {
        document.getElementById("heartbeat").textContent =
            `${health.status} (${health.age_seconds.toFixed(1)}s ago)`;
    }

    // RF
    const rf = await fetchJSON("/rf/status");
    if (rf) {
        document.getElementById("rf-rate").textContent =
            `${rf.frame_rate_hz.toFixed(2)} Hz`;
    }

    // ESP32
    const esp = await fetchJSON("/arduino/esp32");
    if (esp) {
        document.getElementById("esp32-status").textContent =
            `${esp.status} (queue ${esp.queue_pressure})`;
    }

    // Alfa RTL88xx
    const alfa = await fetchJSON("/rf/alfa");
    if (alfa) {
        document.getElementById("alfa-status").textContent =
            `${alfa.status} (${alfa.devices} devices)`;
    }

    // System
    const sys = await fetchJSON("/system/info");
    if (sys) {
        document.getElementById("cpu-load").textContent =
            `${sys.cpu_percent}%`;
        document.getElementById("memory").textContent =
            `${(sys.memory_mb).toFixed(1)} MB`;
    }

    // Telemetry log
    const log = await fetchJSON("/telemetry/recent");
    if (log) {
        const box = document.getElementById("telemetry-log");
        box.innerHTML = log.map(l => `<div>${l}</div>`).join("");
        box.scrollTop = box.scrollHeight;
    }
}

setInterval(updateDashboard, 1000);
updateDashboard();

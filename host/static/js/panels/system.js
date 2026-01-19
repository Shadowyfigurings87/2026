// SYSTEM PANEL LOGIC

async function updateSystemPanel() {
    try {
        const t = await fetch("/system/cpu_temp").then(r => r.json());
        const d = await fetch("/system/db_latency").then(r => r.json());

        document.getElementById("cpu-temp").innerText =
            t.cpu_temp_c === null ? "--" : t.cpu_temp_c.toFixed(1) + "°C";

        document.getElementById("db-latency").innerText =
            d.latency_ms?.toFixed(2) + " ms";

        document.getElementById("db-writes").innerText =
            d.writes_total ?? "--";

        document.getElementById("db-errors").innerText =
            d.write_errors ?? "--";

    } catch (e) {
        console.error("System panel update failed", e);
    }
}

setInterval(updateSystemPanel, 500);

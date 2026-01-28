// RF PANEL LOGIC

window.initRFPanel = function () {

    async function updateRFPanel() {
        try {
            const data = await fetch("/rf/status").then(r => r.json());

            document.getElementById("rf-frame-rate").innerText =
                data.frame_rate_hz?.toFixed(2) ?? "--";

            document.getElementById("rf-total-frames").innerText =
                data.total_frames ?? "--";

            const log = document.getElementById("rf-log");
            if (data.last_frame) {
                const entry = document.createElement("div");
                entry.textContent = JSON.stringify(data.last_frame);
                log.prepend(entry);
            }

        } catch (e) {
            console.error("RF panel update failed", e);
        }
    }

    async function refreshRfPanel() {
        const res = await fetch("/rf/status");
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById("rf-link").textContent = data.link;
        document.getElementById("rf-rssi").textContent = data.rssi;
        document.getElementById("rf-packets-tx").textContent = data.packets_tx;
        document.getElementById("rf-packets-rx").textContent = data.packets_rx;
        document.getElementById("rf-last-heard").textContent =
            data.last_heard_seconds.toFixed(2);
    }

    // Run immediately
    refreshRfPanel();
    updateRFPanel();

    // Then run on intervals
    setInterval(refreshRfPanel, 1000);
    setInterval(updateRFPanel, 1000);
};

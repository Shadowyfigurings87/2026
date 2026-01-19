// RF PANEL LOGIC

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

setInterval(updateRFPanel, 500);

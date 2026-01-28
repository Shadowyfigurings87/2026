window.initESP32Panel = function () {
    const statusEl = document.getElementById("esp32-status");
    const queueEl = document.getElementById("esp32-queue");
    const tsEl = document.getElementById("esp32-ts");
    const rawEl = document.getElementById("esp32-raw");

    async function updateESP32() {
        try {
            // Corrected API route
            const res = await fetch("/esp32");
            if (!res.ok) {
                throw new Error("HTTP " + res.status);
            }

            const data = await res.json();

            statusEl.textContent = data.status ?? "--";
            queueEl.textContent = data.queue_pressure ?? "--";
            tsEl.textContent = data.ts ?? "--";
            rawEl.textContent = JSON.stringify(data.raw, null, 2);

        } catch (err) {
            statusEl.textContent = "error";
            queueEl.textContent = "--";
            tsEl.textContent = "--";
            rawEl.textContent = "Error fetching ESP32 data";
        }
    }

    updateESP32();
    setInterval(updateESP32, 1000);
};

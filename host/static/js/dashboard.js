// ------------------------------
// Initialize MJPEG Stream (cache‑buster)
// ------------------------------
document.addEventListener("DOMContentLoaded", () => {
    const mjpeg = document.getElementById("mjpeg-stream");
    if (mjpeg) {
        mjpeg.src = "/camera/stream?cache=" + Date.now();
    }
});

// ------------------------------
// Utility: Safe JSON fetch
// ------------------------------
async function fetchJSON(url) {
    try {
        const res = await fetch(url, { cache: "no-store" });
        if (!res.ok) return null;
        return await res.json();
    } catch (err) {
        return null;
    }
}

// ------------------------------
// Update Heartbeat Panel
// ------------------------------
async function updateHeartbeat() {
    const data = await fetchJSON("/health");
    const el = document.getElementById("heartbeat");

    if (!data) {
        el.textContent = "offline";
        el.style.color = "#ff4444";
        return;
    }

    el.textContent = `${data.status} (${data.age_seconds.toFixed(1)}s)`;
    el.style.color = data.age_seconds < 5 ? "#44ff44" : "#ffaa00";
}

// ------------------------------
// Update RF Panel
// ------------------------------
async function updateRF() {
    const data = await fetchJSON("/rf/status");
    const el = document.getElementById("rf-rate");

    if (!data) {
        el.textContent = "--";
        return;
    }

    el.textContent = `${data.frame_rate_hz.toFixed(2)} Hz`;
}

// ------------------------------
// Update ESP32 Panel
// ------------------------------
async function updateESP32() {
    const data = await fetchJSON("/arduino/esp32");
    const el = document.getElementById("esp32-status");

    if (!data) {
        el.textContent = "--";
        return;
    }

    el.textContent = `${data.status} (queue ${data.queue_pressure})`;
}

// ------------------------------
// Update Alfa RTL88xx Panel
// ------------------------------
async function updateAlfa() {
    const data = await fetchJSON("/rf/alfa");
    const el = document.getElementById("alfa-status");

    if (!data) {
        el.textContent = "--";
        return;
    }

    el.textContent = `${data.status} (${data.devices} devices)`;
}

// ------------------------------
// Update System Panel
// ------------------------------
async function updateSystem() {
    const data = await fetchJSON("/system/info");

    if (!data) return;

    document.getElementById("cpu-load").textContent =
        `${data.cpu_percent}%`;

    document.getElementById("memory").textContent =
        `${data.memory_mb.toFixed(1)} MB`;
}

// ------------------------------
// Update Telemetry Log
// ------------------------------
async function updateTelemetry() {
    const data = await fetchJSON("/telemetry/recent");
    const box = document.getElementById("telemetry-log");

    if (!data) return;

    box.innerHTML = data.map(line => `<div>${line}</div>`).join("");
    box.scrollTop = box.scrollHeight;
}

// ------------------------------
// Refresh Latest Frame Viewer
// ------------------------------
function updateLatestFrame() {
    const img = document.getElementById("camera-feed");
    img.src = `/camera/latest?ts=${Date.now()}`;
}

// ======================================================
// 🚀 NEW JSON COMMAND API (FINAL VERSION)
// ======================================================

function sendThrottle(value) {
    fetch('/command/throttle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ value: parseFloat(value) })
    });
}

function sendDirection(dir) {
    fetch('/command/direction', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ direction: dir })
    });
}

function sendStop() {
    fetch('/command/stop', { method: 'POST' });
}

function sendCustom() {
    const payload = JSON.parse(document.getElementById('custom-json').value);
    fetch('/command/custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ payload })
    });
}

// ======================================================
// 🚀 BUTTON CONTROLS (NOW USING JSON COMMAND API)
// ======================================================

const throttleSlider = document.getElementById("throttle");

document.getElementById("btn-forward").onclick = () => {
    const speed = throttleSlider.value;
    sendThrottle(speed);
    sendDirection("fwd");
};

document.getElementById("btn-reverse").onclick = () => {
    const speed = throttleSlider.value;
    sendThrottle(speed);
    sendDirection("rev");
};

document.getElementById("btn-dir-fwd").onclick = () => {
    sendDirection("fwd");
};

document.getElementById("btn-dir-rev").onclick = () => {
    sendDirection("rev");
};

document.getElementById("btn-stop").onclick = () => {
    sendStop();
};

// Throttle slider (JSON)
throttleSlider.oninput = (e) => {
    const speed = e.target.value;
    sendThrottle(speed);
};

// ======================================================
// 🚀 DRIVE MODE SYSTEM
// ======================================================

let driveMode = "cruise";  // default

const driveModes = {
    crawl:  { max: 80,  accel: 3 },
    cruise: { max: 160, accel: 5 },
    boost:  { max: 255, accel: 10 }
};

function setDriveMode(mode) {
    driveMode = mode;

    document.querySelectorAll(".drive-mode-btn")
        .forEach(btn => btn.classList.remove("active"));

    const active = document.getElementById(`mode-${mode}`);
    if (active) active.classList.add("active");
}

const btnCrawl  = document.getElementById("mode-crawl");
const btnCruise = document.getElementById("mode-cruise");
const btnBoost  = document.getElementById("mode-boost");

if (btnCrawl)  btnCrawl.onclick  = () => setDriveMode("crawl");
if (btnCruise) btnCruise.onclick = () => setDriveMode("cruise");
if (btnBoost)  btnBoost.onclick  = () => setDriveMode("boost");

setDriveMode("cruise");

// ======================================================
// 🚀 KEYBOARD CONTROLS (JSON COMMAND VERSION)
// ======================================================

let throttle = 0;
let throttleInterval = null;
window.shiftKeyDown = false;

function startThrottle(direction) {
    if (throttleInterval) return;

    throttleInterval = setInterval(() => {
        const mode = driveModes[driveMode];

        if (driveMode === "boost" && !window.shiftKeyDown) return;

        throttle = Math.min(mode.max, throttle + mode.accel);
        throttleSlider.value = throttle;

        sendThrottle(throttle);
        sendDirection(direction);

    }, 100);
}

function stopThrottle() {
    clearInterval(throttleInterval);
    throttleInterval = null;
    throttle = 0;
    throttleSlider.value = 0;
    sendStop();
}

document.addEventListener("keydown", (e) => {
    if (e.repeat) return;

    if (e.key === "Shift") window.shiftKeyDown = true;

    if (e.key === "w") startThrottle("fwd");
    if (e.key === "s") startThrottle("rev");
    if (e.key === "a") sendDirection("rev");
    if (e.key === "d") sendDirection("fwd");
    if (e.key === " ") stopThrottle();
});

document.addEventListener("keyup", (e) => {
    if (e.key === "Shift") window.shiftKeyDown = false;
    if (e.key === "w" || e.key === "s") stopThrottle();
});

// ======================================================
// 🚀 MAIN UPDATE LOOP
// ======================================================

async function updateDashboard() {
    updateLatestFrame();
    updateHeartbeat();
    updateRF();
    updateESP32();
    updateAlfa();
    updateSystem();
    updateTelemetry();
}

updateDashboard();
setInterval(updateDashboard, 1000);

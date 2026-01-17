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

// ------------------------------
// Arduino Command Sender
// ------------------------------
async function sendCommand(cmd) {
    try {
        await fetch("/arduino/command", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ cmd })
        });
    } catch (err) {
        // Silent fail for now; could add UI error later
    }
}

// ------------------------------
// Button Controls
// ------------------------------
const throttleSlider = document.getElementById("throttle");

document.getElementById("btn-forward").onclick = () => {
    const speed = throttleSlider.value;
    sendCommand(`ACT:FWD:${speed}`);
};

document.getElementById("btn-reverse").onclick = () => {
    const speed = throttleSlider.value;
    sendCommand(`ACT:REV:${speed}`);
};

document.getElementById("btn-dir-fwd").onclick = () => {
    sendCommand("DIR:FWD");
};

document.getElementById("btn-dir-rev").onclick = () => {
    sendCommand("DIR:REV");
};

document.getElementById("btn-stop").onclick = () => {
    sendCommand("ACT:STOP");
};

// ------------------------------
// Throttle Slider (PWM direct)
// ------------------------------
throttleSlider.oninput = (e) => {
    const speed = e.target.value;
    sendCommand(`PWM:${speed}`);
};

// ------------------------------
// Drive Mode System
// ------------------------------
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

// Initialize default mode highlight
setDriveMode("cruise");

// ------------------------------
// Keyboard Controls + Throttle Ramping
// ------------------------------
let throttle = 0;
let throttleInterval = null;
window.shiftKeyDown = false;

function startThrottle(direction) {
    if (throttleInterval) return;

    throttleInterval = setInterval(() => {
        const mode = driveModes[driveMode];

        // Boost requires SHIFT held
        if (driveMode === "boost" && !window.shiftKeyDown) return;

        throttle = Math.min(mode.max, throttle + mode.accel);
        throttleSlider.value = throttle;

        if (direction === "fwd")
            sendCommand(`ACT:FWD:${throttle}`);
        else
            sendCommand(`ACT:REV:${throttle}`);
    }, 100);
}

function stopThrottle() {
    clearInterval(throttleInterval);
    throttleInterval = null;
    throttle = 0;
    throttleSlider.value = 0;
    sendCommand("ACT:STOP");
}

document.addEventListener("keydown", (e) => {
    if (e.repeat) return;

    if (e.key === "Shift") window.shiftKeyDown = true;

    if (e.key === "w") startThrottle("fwd");
    if (e.key === "s") startThrottle("rev");
    if (e.key === "a") sendCommand("DIR:REV");
    if (e.key === "d") sendCommand("DIR:FWD");
    if (e.key === " ") stopThrottle();
});

document.addEventListener("keyup", (e) => {
    if (e.key === "Shift") window.shiftKeyDown = false;
    if (e.key === "w" || e.key === "s") stopThrottle();
});

// ------------------------------
// Main Update Loop
// ------------------------------
async function updateDashboard() {
    updateLatestFrame();
    updateHeartbeat();
    updateRF();
    updateESP32();
    updateAlfa();
    updateSystem();
    updateTelemetry();
}

// Run once immediately
updateDashboard();

// Run every second
setInterval(updateDashboard, 1000);

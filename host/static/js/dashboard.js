// ===============================
// WINDOW MANAGER
// ===============================

let zIndexCounter = 10;

// Load a panel by name (camera, telemetry, rf, system, commands, events)
function openPanel(name) {
    fetch(`/static/panels/${name}.html`)
        .then(r => r.text())
        .then(html => createWindow(name, html))
        .catch(err => console.error("Failed to load panel:", name, err));
}

function createWindow(name, html) {
    const win = document.createElement("div");
    win.className = "window";
    win.style.left = "200px";
    win.style.top = "80px";
    win.style.zIndex = zIndexCounter++;

    // Base window structure
    win.innerHTML = `
        <div class="window-titlebar">
            <span>${name.toUpperCase()}</span>
            <button class="close-btn" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
        <div class="window-content"></div>
    `;

    const content = win.querySelector(".window-content");

    // ===============================
    // SAFE HTML INSERTION (CRITICAL)
    // ===============================
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");

    // Insert parsed nodes exactly as written
    content.append(...doc.body.childNodes);

    // ===============================
    // SCRIPT LOADER (GUARANTEED EXECUTION)
    // ===============================
    const scriptRegex = /<script\b[^>]*>([\s\S]*?)<\/script>/gi;
    let match;

    while ((match = scriptRegex.exec(html))) {
        const scriptTag = match[0];
        const srcMatch = scriptTag.match(/src="([^"]+)"/);

        const newScript = document.createElement("script");

        if (srcMatch) {
            // External script
            newScript.src = srcMatch[1] + "?v=" + Date.now(); // cache-bust
        } else {
            // Inline script
            newScript.textContent = match[1];
        }

        document.body.appendChild(newScript);
    }


    // ===============================
    // PANEL INITIALIZERS
    // ===============================
    if (name === "telemetry") {
        // Delay to allow telemetry.js to load and execute
        setTimeout(() => {
            if (typeof startTelemetryPanel === "function") {
                startTelemetryPanel();
            } else {
                console.warn("Telemetry panel script not ready yet");
            }
        }, 50);
    }

    document.getElementById("window-area").appendChild(win);
    makeDraggable(win);
}

// ===============================
// DRAGGABLE WINDOWS
// ===============================

function makeDraggable(win) {
    const bar = win.querySelector(".window-titlebar");
    let offsetX = 0, offsetY = 0, dragging = false;

    bar.addEventListener("mousedown", e => {
        dragging = true;
        offsetX = e.clientX - win.offsetLeft;
        offsetY = e.clientY - win.offsetTop;
        win.style.zIndex = zIndexCounter++;
    });

    document.addEventListener("mousemove", e => {
        if (!dragging) return;
        win.style.left = (e.clientX - offsetX) + "px";
        win.style.top = (e.clientY - offsetY) + "px";
    });

    document.addEventListener("mouseup", () => dragging = false);
}

// ===============================
// TOP BAR METRICS
// ===============================

async function updateTopBar() {
    try {
        const q = await fetch("/telemetry/queue_depth").then(r => r.json());
        const i = await fetch("/telemetry/ingestion_rate").then(r => r.json());
        const h = await fetch("/telemetry/rover_heartbeat").then(r => r.json());

        document.getElementById("queue-depth-top").innerText = "Queue: " + q.queue_depth;
        document.getElementById("ingestion-rate-top").innerText = "Ingest: " + i.ingestion_rate;
        document.getElementById("heartbeat-top").innerText = "Heartbeat: " + h.age_seconds;

    } catch (e) {
        console.error("Top bar update failed", e);
    }
}

setInterval(updateTopBar, 500);
updateTopBar();

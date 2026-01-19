// ===============================
// WINDOW MANAGER
// ===============================

let zIndexCounter = 10;

function openPanel(name) {
    fetch(`/static/panels/${name}.html`)
        .then(r => r.text())
        .then(html => createWindow(name, html));
}

function createWindow(name, html) {
    const win = document.createElement("div");
    win.className = "window";
    win.style.left = "200px";
    win.style.top = "80px";
    win.style.zIndex = zIndexCounter++;

    win.innerHTML = `
        <div class="window-titlebar">
            <span>${name.toUpperCase()}</span>
            <button class="close-btn" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
        <div class="window-content">${html}</div>
    `;

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
        const c = await fetch("/camera/fps").then(r => r.json());

        document.getElementById("queue-depth-top").innerText = "Queue: " + q.queue_depth;
        document.getElementById("ingestion-rate-top").innerText = "Ingest: " + i.ingestion_rate;
        document.getElementById("heartbeat-top").innerText = "Heartbeat: " + h.age_seconds;
        document.getElementById("camera-fps-top").innerText = "FPS: " + c.fps;

    } catch (e) {
        console.error("Top bar update failed", e);
    }
}

setInterval(updateTopBar, 500);

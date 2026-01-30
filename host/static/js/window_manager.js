// =======================================================
// ADVANCED WINDOW MANAGER
// Floating, draggable, resizable, snapping windows
// =======================================================

let zCounter = 10;
let windowCount = 0;

// Bring a window to the front
function bringToFront(win) {
    zCounter += 1;
    win.style.zIndex = zCounter;
}

// Load panel HTML from /static/panels/<name>.html
async function loadPanelHTML(name) {
    const res = await fetch(`/static/panels/${name}.html`);
    if (!res.ok) {
        return `<div class="panel-error">Panel "${name}" not found.</div>`;
    }
    return await res.text();
}

// Create a floating window
function createWindow(name, html) {
    const win = document.createElement("div");
    win.className = "floating-window";
    win.style.zIndex = zCounter;

    // Smart cascading placement
    const offset = (windowCount * 30) % 200;
    win.style.left = `${80 + offset}px`;
    win.style.top = `${80 + offset}px`;
    windowCount++;

    win.innerHTML = `
        <div class="window-titlebar">
            <span class="window-title">${name.toUpperCase()}</span>
            <button class="window-close">✕</button>
        </div>
        <div class="window-content">${html}</div>
        <div class="resize-handle resize-se"></div>
        <div class="resize-handle resize-e"></div>
        <div class="resize-handle resize-s"></div>
    `;

    // Close button with cleanup hook
    win.querySelector(".window-close").onclick = () => {
        win.remove();
        if (window.clearActivePanel) window.clearActivePanel(name);

        // Panel-specific cleanup (stopTelemetryPanel, stopGpsPanel, etc.)
        const stopFn = window[`stop${name.charAt(0).toUpperCase() + name.slice(1)}Panel`];
        if (typeof stopFn === "function") stopFn();
    };

    makeDraggable(win);
    makeResizable(win);

    win.addEventListener("mousedown", () => bringToFront(win));

    document.getElementById("window-area").appendChild(win);
    return win;
}

// =======================================================
// DRAGGING
// =======================================================
function makeDraggable(win) {
    const bar = win.querySelector(".window-titlebar");
    let offsetX = 0, offsetY = 0, dragging = false;

    bar.addEventListener("mousedown", (e) => {
        dragging = true;
        offsetX = e.clientX - win.offsetLeft;
        offsetY = e.clientY - win.offsetTop;
        bringToFront(win);
    });

    window.addEventListener("mousemove", (e) => {
        if (!dragging) return;

        let x = e.clientX - offsetX;
        let y = e.clientY - offsetY;

        // Snap to edges
        if (Math.abs(x) < 15) x = 0;
        if (Math.abs(y) < 15) y = 0;

        // Snap to grid (20px)
        x = Math.round(x / 20) * 20;
        y = Math.round(y / 20) * 20;

        win.style.left = `${x}px`;
        win.style.top = `${y}px`;
    });

    window.addEventListener("mouseup", () => dragging = false);
}

// =======================================================
// RESIZING
// =======================================================
function makeResizable(win) {
    const handles = win.querySelectorAll(".resize-handle");

    handles.forEach(handle => {
        let resizing = false;
        let startX, startY, startW, startH;

        handle.addEventListener("mousedown", (e) => {
            e.stopPropagation();
            resizing = true;
            bringToFront(win);

            startX = e.clientX;
            startY = e.clientY;
            startW = win.offsetWidth;
            startH = win.offsetHeight;
        });

        window.addEventListener("mousemove", (e) => {
            if (!resizing) return;

            if (handle.classList.contains("resize-e")) {
                win.style.width = `${startW + (e.clientX - startX)}px`;
            }
            if (handle.classList.contains("resize-s")) {
                win.style.height = `${startH + (e.clientY - startY)}px`;
            }
            if (handle.classList.contains("resize-se")) {
                win.style.width = `${startW + (e.clientX - startX)}px`;
                win.style.height = `${startH + (e.clientY - startY)}px`;
            }
        });

        window.addEventListener("mouseup", () => resizing = false);
    });
}

// =======================================================
// OPEN PANEL
// =======================================================
async function openPanel(name) {
    const html = await loadPanelHTML(name);

    // Create window and wait for next paint cycle
    const win = createWindow(name, html);
    await new Promise(requestAnimationFrame);

    // Now the DOM is guaranteed ready
    window.dispatchEvent(new CustomEvent("panel-loaded", { detail: name }));
    if (window.setActivePanel) window.setActivePanel(name);

    return win;
}

// =======================================================
// EXPORT GLOBALS
// =======================================================
window.openPanel = openPanel;
window.createWindow = createWindow;
window.makeDraggable = makeDraggable;

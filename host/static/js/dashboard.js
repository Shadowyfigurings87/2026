// =======================================================
// GLOBAL STUBS (defined BEFORE import)
// Ensures inline onclick handlers never throw
// =======================================================

if (!window.openPanel) {
    window.openPanel = function(name) {
        console.warn("openPanel() called before window manager loaded:", name);
    };
}

if (!window.createWindow) {
    window.createWindow = function() {
        console.warn("createWindow() called before window manager loaded");
    };
}

// =======================================================
// IMPORT WINDOW MANAGER (guaranteed to overwrite stubs)
// =======================================================


// =======================================================
// DASHBOARD CORE LOGIC
// =======================================================

let activePanel = null;

window.setActivePanel = function(name) {
    activePanel = name;
    console.log("Active panel:", name);
};

window.clearActivePanel = function(name) {
    if (activePanel === name) {
        activePanel = null;
        console.log("Panel closed:", name);
    }
};

// =======================================================
// GLOBAL KEYBOARD ROUTER
// =======================================================

window.addEventListener("keydown", (e) => {
    if (!activePanel) return;

    if (activePanel === "commands" && typeof window.roverKeyHandler === "function") {
        window.roverKeyHandler(e);
    }
});

// =======================================================
// GLOBAL MOUSE WHEEL ROUTER
// =======================================================

window.addEventListener("wheel", (e) => {
    if (!activePanel) return;

    if (activePanel === "commands" && typeof window.roverWheelHandler === "function") {
        window.roverWheelHandler(e);
    }
}, { passive: false });

// =======================================================
// PANEL INITIALIZATION HOOKS (DYNAMIC SCRIPT LOADING)
// =======================================================

async function initializePanel(name) {
    switch (name) {

        case "commands":
            await import("/static/js/panels/commands.js");
            if (typeof window.initCommandsPanel === "function") {
                window.initCommandsPanel();
            }
            break;

        case "telemetry":
            await import("/static/js/panels/telemetry.js");
            if (typeof window.startTelemetryPanel === "function") {
                window.startTelemetryPanel();
            }
            break;

        case "camera":
            await import("/static/js/panels/camera.js");
            if (typeof window.initCameraPanel === "function") {
                window.initCameraPanel();
            }
            break;
        case "esp32":
            await import("/static/js/panels/esp32.js");
            if (typeof window.initESP32Panel === "function") {
                window.initESP32Panel();
            }
            break;
    }
}

window.initializePanel = initializePanel;

// =======================================================
// WINDOW MANAGER HOOK-IN
// =======================================================

window.addEventListener("panel-loaded", (e) => {
    initializePanel(e.detail);
});

// host/static/js/panels/camera.js

let lastFrameTime = null;

const fpsPanel = document.getElementById("camera-fps-panel");
const agePanel = document.getElementById("camera-age-panel");
const cameraImg = document.getElementById("camera-stream");

// ---------------------------------------------------------
// SET MJPEG STREAM SOURCE
// ---------------------------------------------------------
cameraImg.src = "/camera/mjpeg";

// ---------------------------------------------------------
// FRAME ARRIVAL HANDLER
// ---------------------------------------------------------
cameraImg.onload = () => {
    const now = performance.now();

    if (lastFrameTime !== null) {
        const delta = (now - lastFrameTime) / 1000;
        const fps = (1 / delta).toFixed(1);
        fpsPanel.textContent = fps;
    }

    lastFrameTime = now;
};

// ---------------------------------------------------------
// STREAM ERROR HANDLER
// ---------------------------------------------------------
cameraImg.onerror = () => {
    fpsPanel.textContent = "--";
    agePanel.textContent = "--";
};

// ---------------------------------------------------------
// AGE UPDATER
// ---------------------------------------------------------
setInterval(() => {
    if (lastFrameTime === null) {
        agePanel.textContent = "--";
        return;
    }

    const age = ((performance.now() - lastFrameTime) / 1000).toFixed(1);
    agePanel.textContent = age + "s";
}, 1000);

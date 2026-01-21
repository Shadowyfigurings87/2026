// host/static/js/panels/camera.js

let lastFrameTime = null;
let fpsPanel = document.getElementById("camera-fps-panel");
let agePanel = document.getElementById("camera-age-panel");
let cameraImg = document.getElementById("camera-stream");

// Called whenever the <img> element receives a new frame
cameraImg.onload = () => {
    const now = performance.now();

    if (lastFrameTime !== null) {
        const delta = (now - lastFrameTime) / 1000;
        const fps = (1 / delta).toFixed(1);
        fpsPanel.textContent = fps;
    }

    lastFrameTime = now;
};

// Called if the MJPEG stream fails
cameraImg.onerror = () => {
    fpsPanel.textContent = "--";
    agePanel.textContent = "--";
};

// Update "age" every second
setInterval(() => {
    if (lastFrameTime === null) {
        agePanel.textContent = "--";
        return;
    }

    const age = ((performance.now() - lastFrameTime) / 1000).toFixed(1);
    agePanel.textContent = age + "s";
}, 1000);

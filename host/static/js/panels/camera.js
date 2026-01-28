// host/static/js/panels/camera.js

let lastFrameTime = null;

window.initCameraPanel = function () {
    const fpsPanel = document.getElementById("camera-fps-panel");
    const agePanel = document.getElementById("camera-age-panel");
    const cameraImg = document.getElementById("camera-stream");

    if (!cameraImg) {
        console.error("Camera panel: #camera-stream not found");
        return;
    }

    // ---------------------------------------------------------
    // SET MJPEG STREAM SOURCE
    // ---------------------------------------------------------
    cameraImg.src = "/camera/mjpeg";

    // ---------------------------------------------------------
    // BACKEND FPS POLLER
    // ---------------------------------------------------------
    async function updateBackendFPS() {
        try {
            const res = await fetch("/camera/fps");
            const data = await res.json();
            fpsPanel.textContent = data.fps ?? "--";
        } catch {
            fpsPanel.textContent = "--";
        }
    }

    setInterval(updateBackendFPS, 500);

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
};

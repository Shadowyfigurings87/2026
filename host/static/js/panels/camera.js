// CAMERA PANEL LOGIC

async function updateCameraPanel() {
    try {
        const res = await fetch("/camera/fps");
        if (!res.ok) return;

        const data = await res.json();

        // Update FPS
        const fpsEl = document.getElementById("camera-fps-panel");
        if (fpsEl) fpsEl.innerText = data.fps.toFixed(2);

        // Update Age
        const ageEl = document.getElementById("camera-age-panel");
        if (ageEl) {
            ageEl.innerText =
                data.age_seconds === null
                    ? "--"
                    : data.age_seconds.toFixed(2) + "s";
        }

    } catch (err) {
        console.error("Camera panel update failed:", err);
    }
}

// Update twice per second
setInterval(updateCameraPanel, 500);
updateCameraPanel();

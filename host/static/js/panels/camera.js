// CAMERA PANEL LOGIC

async function updateCameraPanel() {
    try {
        const data = await fetch("/camera/fps").then(r => r.json());

        document.getElementById("camera-fps-panel").innerText = data.fps.toFixed(2);
        document.getElementById("camera-age-panel").innerText =
            data.age_seconds === null ? "--" : data.age_seconds.toFixed(2) + "s";

    } catch (e) {
        console.error("Camera panel update failed", e);
    }
}

setInterval(updateCameraPanel, 500);

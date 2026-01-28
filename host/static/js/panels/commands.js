// =======================================================
//  ROVER COMMAND PANEL LOGIC
// =======================================================

window.initCommandsPanel = function () {

    // --- Core command emitter ---
    function sendCommand(obj) {
        fetch("/commands/send", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(obj)
        }).catch(err => console.error("Command send failed", err));
    }

    // --- State ---
    const state = {
        active: false,
        throttle: 0,
        mode: "crawl",
        steeringSpeed: 160,
        direction: "STOP"
    };

    // --- DOM refs ---
    const panel = document.getElementById("rover-panel");
    const throttleSlider = document.getElementById("throttle");
    const throttleValue = document.getElementById("command-throttle-value");

    const btnForward = document.getElementById("btn-forward");
    const btnReverse = document.getElementById("btn-reverse");
    const btnStop = document.getElementById("btn-stop");
    const btnDirFwd = document.getElementById("btn-dir-fwd");
    const btnDirRev = document.getElementById("btn-dir-rev");

    const modeButtons = {
        crawl: document.getElementById("mode-crawl"),
        cruise: document.getElementById("mode-cruise"),
        boost: document.getElementById("mode-boost")
    };

    const statusLine = document.getElementById("status-line");

    // =======================================================
    //  PANEL FOCUS CONTROL
    // =======================================================

    panel.addEventListener("click", () => setPanelActive(true));

    document.addEventListener("click", e => {
        if (!panel.contains(e.target)) setPanelActive(false);
    });

    function setPanelActive(active) {
        state.active = active;
        panel.classList.toggle("inactive", !active);
        statusLine.textContent = active
            ? "Panel active: keyboard & mouse wheel bound to rover."
            : "Panel inactive. Click inside to arm controls.";
    }

    // =======================================================
    //  MODE CONTROL
    // =======================================================

    function setMode(mode) {
        state.mode = mode;

        Object.keys(modeButtons).forEach(m => {
            modeButtons[m].classList.toggle("active", m === mode);
        });

        let preset = 80;
        if (mode === "cruise") preset = 150;
        if (mode === "boost") preset = 220;

        setThrottle(preset);
        sendCommand({mode});
    }

    modeButtons.crawl.onclick = () => setMode("crawl");
    modeButtons.cruise.onclick = () => setMode("cruise");
    modeButtons.boost.onclick = () => setMode("boost");

    // =======================================================
    //  THROTTLE CONTROL
    // =======================================================

    function setThrottle(value) {
        value = Math.max(0, Math.min(255, value));
        state.throttle = value;

        throttleSlider.value = value;
        throttleValue.textContent = value;

        sendCommand({throttle: value});
    }

    throttleSlider.oninput = e => setThrottle(Number(e.target.value));

    panel.addEventListener("wheel", e => {
        if (!state.active) return;
        e.preventDefault();

        const step = 10;
        const delta = e.deltaY < 0 ? step : -step;

        setThrottle(state.throttle + delta);
    }, { passive: false });

    // =======================================================
    //  DRIVE DIRECTION
    // =======================================================

    function setDriveDirection(dir) {
        state.direction = dir;

        btnForward.classList.toggle("active", dir === "FWD");
        btnReverse.classList.toggle("active", dir === "REV");
        btnStop.classList.toggle("active", dir === "STOP");

        if (dir === "FWD") sendCommand({move: "forward"});
        if (dir === "REV") sendCommand({move: "reverse"});
        if (dir === "STOP") sendCommand({stop: true});
    }

    btnForward.onclick = () => setDriveDirection("FWD");
    btnReverse.onclick = () => setDriveDirection("REV");
    btnStop.onclick = () => setDriveDirection("STOP");

    // =======================================================
    //  STEERING ACTUATOR
    // =======================================================

    function steerLeft() {
        btnDirRev.classList.add("active");
        btnDirFwd.classList.remove("active");
        sendCommand({actuator: {dir: "REV", speed: state.steeringSpeed}});
    }

    function steerRight() {
        btnDirFwd.classList.add("active");
        btnDirRev.classList.remove("active");
        sendCommand({actuator: {dir: "FWD", speed: state.steeringSpeed}});
    }

    btnDirFwd.onclick = () => steerRight();
    btnDirRev.onclick = () => steerLeft();

    // =======================================================
    //  KEYBOARD BINDINGS
    // =======================================================

    window.roverKeyHandler = function (e) {
        if (!state.active) return;

        switch (e.key) {
            case "1": setMode("crawl"); break;
            case "2": setMode("cruise"); break;
            case "3": setMode("boost"); break;

            case "f":
            case "F":
                setDriveDirection("FWD");
                break;

            case "r":
            case "R":
                setDriveDirection("REV");
                break;

            case " ":
                e.preventDefault();
                setDriveDirection("STOP");
                break;

            case "ArrowUp":
                setThrottle(state.throttle + 10);
                break;

            case "ArrowDown":
                setThrottle(state.throttle - 10);
                break;

            case "ArrowLeft":
                steerLeft();
                break;

            case "ArrowRight":
                steerRight();
                break;
        }
    };

    // =======================================================
    //  INITIAL STATE
    // =======================================================

    setMode("crawl");
    setDriveDirection("STOP");
    setPanelActive(false);
};

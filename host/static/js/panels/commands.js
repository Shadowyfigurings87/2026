// COMMAND PANEL LOGIC

function sendCommand(obj) {
    fetch("/commands/send", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(obj)
    }).catch(err => console.error("Command send failed", err));
}

// Drive mode buttons
document.getElementById("mode-crawl").onclick = () => sendCommand({mode: "crawl"});
document.getElementById("mode-cruise").onclick = () => sendCommand({mode: "cruise"});
document.getElementById("mode-boost").onclick = () => sendCommand({mode: "boost"});

// Movement
document.getElementById("btn-forward").onclick = () => sendCommand({move: "forward"});
document.getElementById("btn-reverse").onclick = () => sendCommand({move: "reverse"});

// Direction
document.getElementById("btn-dir-fwd").onclick = () => sendCommand({direction: "forward"});
document.getElementById("btn-dir-rev").onclick = () => sendCommand({direction: "reverse"});

// Throttle slider
document.getElementById("throttle").oninput = e =>
    sendCommand({throttle: Number(e.target.value)});

// Stop button
document.getElementById("btn-stop").onclick = () => sendCommand({stop: true});

// Custom JSON
document.getElementById("send-custom-btn").onclick = () => {
    try {
        const obj = JSON.parse(document.getElementById("custom-json").value);
        sendCommand(obj);
    } catch (e) {
        alert("Invalid JSON");
    }
};

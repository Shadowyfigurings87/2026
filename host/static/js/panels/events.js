// EVENT LOG PANEL LOGIC

async function updateEventLogPanel() {
    try {
        const events = await fetch("/events/latest").then(r => r.json());

        const log = document.getElementById("event-log");

        events.forEach(ev => {
            const entry = document.createElement("div");
            entry.textContent = `[${ev.ts}] ${ev.type}: ${ev.message}`;
            log.prepend(entry);
        });

    } catch (e) {
        console.error("Event log update failed", e);
    }
}

setInterval(updateEventLogPanel, 1000);

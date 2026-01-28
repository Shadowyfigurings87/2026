// EVENT LOG PANEL LOGIC

window.initEventLogPanel = function () {

    async function updateEventLogPanel() {
        try {
            const events = await fetch("/events/latest").then(r => r.json());

            const log = document.getElementById("event-log");
            if (!log) {
                console.error("Event log panel: #event-log not found");
                return;
            }

            events.forEach(ev => {
                const entry = document.createElement("div");
                entry.textContent = `[${ev.ts}] ${ev.type}: ${ev.message}`;
                log.prepend(entry);
            });

        } catch (e) {
            console.error("Event log update failed", e);
        }
    }

    // Run immediately
    updateEventLogPanel();

    // Then run every second
    setInterval(updateEventLogPanel, 1000);
};

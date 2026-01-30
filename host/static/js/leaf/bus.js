// static/js/leaf/bus.js
export class LeafBus {
    constructor() {
        this.listeners = {}
    }

    on(event, handler) {
        if (!this.listeners[event]) this.listeners[event] = []
        this.listeners[event].push(handler)
    }

    emit(event, payload) {
        if (this.listeners[event]) {
            for (const fn of this.listeners[event]) {
                try {
                    fn(payload)
                } catch (err) {
                    console.error("LeafBus handler error for", event, err)
                }
            }
        }
    }
}

// static/js/leaf/state.js

export class LeafState {
    constructor() {
        this.store = {};
        this.subscribers = {};   // { key: [callback, callback] }
    }

    // Set a value and notify subscribers
    set(key, value) {
        this.store[key] = value;

        if (this.subscribers[key]) {
            for (const cb of this.subscribers[key]) {
                try {
                    cb(value);
                } catch (err) {
                    console.error("LeafState subscriber error:", err);
                }
            }
        }
    }

    // Get a value
    get(key) {
        return this.store[key];
    }

    // Subscribe to changes for a specific key
    subscribe(key, callback) {
        if (!this.subscribers[key]) {
            this.subscribers[key] = [];
        }
        this.subscribers[key].push(callback);

        // Immediately fire with current value if exists
        if (key in this.store) {
            callback(this.store[key]);
        }
    }
}

// static/js/leaf/state.js
export class LeafState {
    constructor() {
        this.data = {}
    }

    set(key, value) {
        this.data[key] = value
        document.dispatchEvent(new CustomEvent(`leaf:update:${key}`, { detail: value }))
    }

    get(key) {
        return this.data[key]
    }
}

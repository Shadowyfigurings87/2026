// mapping/frontend/main.js

const MAP_STYLE_URL = "http://localhost:5000/style.json";

const map = new maplibregl.Map({
    container: "map",
    style: MAP_STYLE_URL,
    center: [-81.6557, 30.3322], // Jacksonville
    zoom: 10,
    hash: true
});

// Optional: add navigation controls
map.addControl(new maplibregl.NavigationControl(), "top-right");

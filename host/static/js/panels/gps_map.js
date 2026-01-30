// static/js/panels/gps_map.js

function waitForLeaf(callback) {
    if (window.leaf && window.leaf.state) {
        callback(window.leaf);
        return;
    }
    console.warn("[GPSMapPanel] Leaf not ready, retrying...");
    setTimeout(() => waitForLeaf(callback), 50);
}

waitForLeaf((leaf) => {
    console.log("[GPSMapPanel] Leaf ready.");

    let map = null;
    let marker = null;
    let initialized = false;

    function initGpsPanel() {
        if (initialized) return;
        initialized = true;

        const container = document.getElementById("gps-map");
        if (!container) {
            console.warn("[GPSMapPanel] #gps-map not found (panel not ready)");
            initialized = false;
            return;
        }

        if (typeof mapboxgl === "undefined") {
            console.error("gps_map: mapboxgl is not loaded");
            return;
        }

        mapboxgl.accessToken = window.MAPBOX_TOKEN || "<YOUR_MAPBOX_TOKEN_HERE>";

        const defaultCenter = [-81.6928586, 30.3347721];

        map = new mapboxgl.Map({
            container: "gps-map",
            style: "mapbox://styles/mapbox/streets-v11",
            center: defaultCenter,
            zoom: 13,
        });

        marker = new mapboxgl.Marker({ color: "#ff4136" })
            .setLngLat(defaultCenter)
            .addTo(map);
    }

    function updateUI(gps) {
        if (!gps) return;

        const latEl = document.getElementById("gps-lat");
        const lonEl = document.getElementById("gps-lon");
        const tsEl  = document.getElementById("gps-timestamp");

        if (latEl) latEl.textContent = gps.lat?.toFixed(6) ?? "--";
        if (lonEl) lonEl.textContent = gps.lon?.toFixed(6) ?? "--";
        if (tsEl)  tsEl.textContent  = gps.timestamp ?? "--";

        if (map && marker && gps.lat && gps.lon) {
            const lngLat = [gps.lon, gps.lat];
            marker.setLngLat(lngLat);
            map.easeTo({ center: lngLat, duration: 800 });
        }
    }

    window.addEventListener("panel-loaded", (e) => {
        if (e.detail === "gps") {
            setTimeout(initGpsPanel, 50);
        }
    });

    leaf.state.subscribe("gps", (gps) => {
        updateUI(gps);
    });

    window.stopGpsPanel = function() {
        initialized = false;
        map = null;
        marker = null;
    };
});

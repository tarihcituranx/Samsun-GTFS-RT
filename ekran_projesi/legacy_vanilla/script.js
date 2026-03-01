/**
 * Samsun Ekran Projesi - Real-Time Vehicle Tracking
 * 100% Gerçek Veri - samsun.py ile uyumlu
 */

const API_BASE = "http://localhost:8001";
const API_URL = `${API_BASE}/api/screen-data`;

// Dynamic line selection
let LINE_CODE = localStorage.getItem('selectedLine') || "26/17";
let MY_STOP_SEQ = parseInt(localStorage.getItem('selectedStop') || "10");

// Global map & markers
let map;
let busMarker = null;
let stopMarkers = {};
let routeLine = null;
let isFirstLoad = true;
let availableLines = [];

// Settings Modal Functions
function openSettings() {
    document.getElementById('settings-modal').classList.add('active');
    loadLineList();
}

function closeSettings() {
    document.getElementById('settings-modal').classList.remove('active');
}

function applySettings() {
    const lineSelect = document.getElementById('line-select');
    const stopSelect = document.getElementById('stop-select');

    if (lineSelect.value) {
        LINE_CODE = lineSelect.value;
        localStorage.setItem('selectedLine', LINE_CODE);
    }

    MY_STOP_SEQ = parseInt(stopSelect.value);
    localStorage.setItem('selectedStop', MY_STOP_SEQ);

    // Update UI
    document.querySelector('.line-badge').textContent = LINE_CODE;

    // Reset map and reload
    isFirstLoad = true;
    if (busMarker) { map.removeLayer(busMarker); busMarker = null; }
    Object.values(stopMarkers).forEach(m => map.removeLayer(m));
    stopMarkers = {};
    if (routeLine) { map.removeLayer(routeLine); routeLine = null; }

    closeSettings();
    updateScreen();
}

async function loadLineList() {
    const select = document.getElementById('line-select');
    select.innerHTML = '<option value="">Yükleniyor...</option>';

    try {
        const response = await fetch(`${API_BASE}/api/lines`);
        const data = await response.json();

        if (data.lines && data.lines.length > 0) {
            availableLines = data.lines;
            select.innerHTML = '';

            data.lines.forEach(line => {
                const option = document.createElement('option');
                option.value = line.code;
                option.textContent = `${line.code} - ${line.name || ''}`;
                if (line.code === LINE_CODE) option.selected = true;
                select.appendChild(option);
            });
        } else {
            // Fallback - some popular lines
            select.innerHTML = `
                <option value="26/17">26/17 - BATIEVLER - ÜNİVERSİTE</option>
                <option value="19">19 - GAZİ - ATAKUM</option>
                <option value="SAMULAŞ - TRAMVAY">Tramvay</option>
                <option value="10">10 - KÖPRÜBAŞI - SANAYİ</option>
            `;
        }
    } catch (e) {
        console.error("Line list error:", e);
        // Fallback
        select.innerHTML = `
            <option value="26/17">26/17 - BATIEVLER - ÜNİVERSİTE</option>
            <option value="19">19 - GAZİ - ATAKUM</option>
            <option value="10">10 - KÖPRÜBAŞI</option>
        `;
    }
}

// Event Carousel
let events = [];
let currentEventIndex = 0;

async function loadEvents() {
    try {
        const response = await fetch(`${API_BASE}/api/events`);
        const data = await response.json();
        if (data.events && data.events.length > 0) {
            events = data.events;
            showEvent(0);
        }
    } catch (e) {
        console.error("Events error:", e);
    }
}

function showEvent(index) {
    if (events.length === 0) return;

    currentEventIndex = index;
    if (currentEventIndex < 0) currentEventIndex = events.length - 1;
    if (currentEventIndex >= events.length) currentEventIndex = 0;

    const event = events[currentEventIndex];
    const card = document.getElementById('current-event');

    // Type color based on category
    const typeColors = {
        'Tiyatro': '#e91e63',
        'Müzik': '#9c27b0',
        'OperaBale': '#3f51b5',
        'default': '#00bcd4'
    };
    const typeColor = typeColors[event.type] || typeColors['default'];

    card.innerHTML = `
        <img class="event-thumb" src="${event.image || ''}" alt="${event.title}" onerror="this.style.display='none'">
        <div class="event-details">
            <div class="event-type" style="color: ${typeColor}">${event.type || 'Etkinlik'}</div>
            <div class="event-title">${event.title}</div>
            <div class="event-info">
                <span class="venue">${event.venue}</span>
                <span class="date">${event.date}, ${event.time}</span>
            </div>
        </div>
    `;
}

function nextEvent() {
    showEvent(currentEventIndex + 1);
}

function prevEvent() {
    showEvent(currentEventIndex - 1);
}

// YouTube Playlist Rotation
const YOUTUBE_PLAYLIST = 'PLLPjJUp5zugqE2zi3n5HQupNQFXU1evV3';
const MAP_DURATION = 45; // seconds to show map
const VIDEO_DURATION = 30; // seconds to show video
const EVENT_IMAGE_DURATION = 15; // seconds to show event image
let mediaMode = 'map'; // 'map', 'video', or 'event_image'
let mediaCountdown = MAP_DURATION;
let currentVideoIndex = 0;

function startMediaRotation() {
    setInterval(() => {
        mediaCountdown--;
        updateMediaCountdown();

        if (mediaCountdown <= 0) {
            cycleMediaMode();
        }
    }, 1000);
}

function cycleMediaMode() {
    const overlay = document.getElementById('media-overlay');
    const player = document.getElementById('youtube-player');

    if (mediaMode === 'map') {
        // Show event image overlay
        if (events.length > 0) {
            mediaMode = 'event_image';
            mediaCountdown = EVENT_IMAGE_DURATION;
            const event = events[currentEventIndex];
            player.style.display = 'none';
            overlay.innerHTML = `
                <div style="width:100%;height:100%;background:linear-gradient(135deg,#1a1a2e,#16213e);display:flex;align-items:center;justify-content:center;flex-direction:column;padding:40px;">
                    <img src="${event.image}" style="max-width:60%;max-height:50%;border-radius:12px;box-shadow:0 10px 40px rgba(0,0,0,0.5);" onerror="this.style.display='none'">
                    <div style="color:#e91e63;font-size:0.9rem;text-transform:uppercase;margin-top:20px;font-weight:bold;">${event.type}</div>
                    <div style="color:#fff;font-size:1.8rem;font-weight:bold;text-align:center;margin:10px 0;">${event.title}</div>
                    <div style="color:#aaa;font-size:1rem;">📍 ${event.venue}</div>
                    <div style="color:#aaa;font-size:1rem;">📅 ${event.date}, ${event.time}</div>
                </div>
                <div class="media-countdown" id="media-countdown">Harita: ${EVENT_IMAGE_DURATION}s</div>
            `;
            overlay.classList.add('active');
            nextEvent(); // Prepare next event for next cycle
        } else {
            // Skip to video if no events
            switchToVideo();
        }
    } else if (mediaMode === 'event_image') {
        // Switch to video
        switchToVideo();
    } else {
        // Switch back to map
        mediaMode = 'map';
        mediaCountdown = MAP_DURATION;
        overlay.classList.remove('active');
        overlay.innerHTML = `
            <iframe id="youtube-player" src="" allow="autoplay; encrypted-media" allowfullscreen></iframe>
            <div class="media-countdown" id="media-countdown">Video: ${MAP_DURATION}s</div>
        `;
    }
}

function switchToVideo() {
    const overlay = document.getElementById('media-overlay');
    mediaMode = 'video';
    mediaCountdown = VIDEO_DURATION;
    currentVideoIndex = (currentVideoIndex + 1) % 5;
    overlay.innerHTML = `
        <iframe id="youtube-player" src="https://www.youtube.com/embed/videoseries?list=${YOUTUBE_PLAYLIST}&index=${currentVideoIndex}&autoplay=1&mute=1&controls=0" allow="autoplay; encrypted-media" allowfullscreen style="width:100%;height:100%;border:none;"></iframe>
        <div class="media-countdown" id="media-countdown">Harita: ${VIDEO_DURATION}s</div>
    `;
    overlay.classList.add('active');
}

function updateMediaCountdown() {
    const el = document.getElementById('media-countdown');
    if (!el) return;
    if (mediaMode === 'map') {
        el.textContent = `Etkinlik: ${mediaCountdown}s`;
    } else if (mediaMode === 'event_image') {
        el.textContent = `Video: ${mediaCountdown}s`;
    } else {
        el.textContent = `Harita: ${mediaCountdown}s`;
    }
}

// Bus Icon (Real bus icon with direction)
function createBusIcon(heading = 0, speed = 0) {
    const color = speed > 30 ? '#00ff00' : speed > 10 ? '#ffc107' : '#ff5722';
    const rotation = heading || 0;
    return L.divIcon({
        html: `<div style="
            font-size: 32px;
            transform: rotate(${rotation}deg);
            text-shadow: 0 0 8px ${color}, 0 0 15px ${color};
            filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5));
        ">🚌</div>`,
        className: 'bus-marker-real',
        iconSize: [40, 40],
        iconAnchor: [20, 20]
    });
}

function createStopIcon(isActive = false, isPassed = false) {
    if (isPassed) {
        return L.divIcon({
            html: `<div style="
                width: 12px; height: 12px;
                background: #666;
                border-radius: 50%;
                border: 2px solid #444;
            "></div>`,
            className: 'stop-passed',
            iconSize: [16, 16],
            iconAnchor: [8, 8]
        });
    }

    const bg = isActive ? '#1a73e8' : '#4CAF50';
    const glow = isActive ? '0 0 10px #1a73e8, 0 0 20px #1a73e8' : 'none';
    const size = isActive ? 24 : 16;

    return L.divIcon({
        html: `<div style="
            width: ${size}px; height: ${size}px;
            background: ${bg};
            border-radius: 50%;
            border: 3px solid #fff;
            box-shadow: ${glow}, 0 2px 8px rgba(0,0,0,0.4);
            ${isActive ? 'animation: pulse 1.5s infinite;' : ''}
        "></div>`,
        className: isActive ? 'stop-active' : 'stop-future',
        iconSize: [size + 6, size + 6],
        iconAnchor: [(size + 6) / 2, (size + 6) / 2]
    });
}

// Initialize Map
function initMap() {
    map = L.map('map', {
        center: [41.2867, 36.33],
        zoom: 14,
        zoomControl: false,
        attributionControl: false
    });

    // Dark theme tiles
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19
    }).addTo(map);

    // Add pulse animation style
    const style = document.createElement('style');
    style.textContent = `
        @keyframes pulse {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.3); opacity: 0.7; }
            100% { transform: scale(1); opacity: 1; }
        }
        .stop-active div { animation: pulse 1.5s infinite; }
    `;
    document.head.appendChild(style);
}

// Update Map with REAL data
function updateMap(data) {
    if (!data || !data.transport) return;

    const transport = data.transport;
    const stops = transport.stops || [];
    const currentBus = transport.current_bus;
    const myStopSeq = MY_STOP_SEQ;

    // 1. Draw Route Polyline
    const coords = stops.filter(s => s.lat && s.lon).map(s => [s.lat, s.lon]);
    if (coords.length > 1) {
        if (routeLine) map.removeLayer(routeLine);
        routeLine = L.polyline(coords, {
            color: '#1a73e8',
            weight: 5,
            opacity: 0.8,
            dashArray: null
        }).addTo(map);
    }

    // 2. Stop Markers (Clear old ones first on first load)
    if (isFirstLoad) {
        Object.values(stopMarkers).forEach(m => map.removeLayer(m));
        stopMarkers = {};
    }

    stops.forEach((stop) => {
        if (!stop.lat || !stop.lon) return;

        const isPassed = stop.seq < myStopSeq;
        const isActive = stop.is_next;
        const key = `stop_${stop.seq}`;

        if (stopMarkers[key]) {
            map.removeLayer(stopMarkers[key]);
        }

        const marker = L.marker([stop.lat, stop.lon], {
            icon: createStopIcon(isActive, isPassed)
        }).addTo(map);

        // Popup with real data
        const etaText = stop.eta === '?' ? 'Hesaplanıyor...' : `${stop.eta} dk`;
        marker.bindPopup(`
            <div style="font-family: Roboto, sans-serif;">
                <b>${stop.name}</b><br>
                <span style="color: #1a73e8;">Tahmini: ${etaText}</span>
            </div>
        `);

        stopMarkers[key] = marker;
    });

    // 3. REAL Bus Marker with movement
    if (currentBus && currentBus.lat && currentBus.lon) {
        const busLatLng = [currentBus.lat, currentBus.lon];

        if (busMarker) {
            // Smooth movement animation
            const currentPos = busMarker.getLatLng();
            animateBusMovement(currentPos, busLatLng, currentBus.heading || 0, currentBus.speed || 0);
        } else {
            busMarker = L.marker(busLatLng, {
                icon: createBusIcon(currentBus.heading || 0, currentBus.speed || 0),
                zIndexOffset: 1000
            }).addTo(map);
        }

        // Bus popup with real info
        busMarker.bindPopup(`
            <div style="font-family: Roboto, sans-serif; min-width: 150px;">
                <b>🚌 ${currentBus.plate || 'Araç'}</b><br>
                <hr style="margin: 5px 0; border: none; border-top: 1px solid #eee;">
                <div style="display: flex; justify-content: space-between;">
                    <span>Hız:</span>
                    <b>${currentBus.speed || 0} km/s</b>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span>Yolcu:</span>
                    <b>${currentBus.passengers || '?'}</b>
                </div>
            </div>
        `);

        // Auto-zoom and follow bus (closer view)
        if (isFirstLoad) {
            map.setView(busLatLng, 17);  // Zoom 17 for close tracking
            isFirstLoad = false;
        } else {
            // Smooth pan to bus
            map.setView(busLatLng, 17, { animate: true, duration: 1.5 });
        }
    } else if (isFirstLoad && coords.length > 0) {
        // No bus found - show route
        map.fitBounds(coords, { padding: [50, 50] });
        isFirstLoad = false;
    }
}

// Animate bus movement
function animateBusMovement(fromLatLng, toLatLng, heading, speed) {
    const steps = 20;
    const duration = 500; // ms
    const latStep = (toLatLng[0] - fromLatLng.lat) / steps;
    const lngStep = (toLatLng[1] - fromLatLng.lng) / steps;

    let step = 0;
    const interval = setInterval(() => {
        step++;
        const newLat = fromLatLng.lat + (latStep * step);
        const newLng = fromLatLng.lng + (lngStep * step);

        if (busMarker) {
            busMarker.setLatLng([newLat, newLng]);
            busMarker.setIcon(createBusIcon(heading, speed));
        }

        if (step >= steps) {
            clearInterval(interval);
        }
    }, duration / steps);
}

// Update Timeline (Right Panel)
function renderTimeline(data) {
    if (!data || !data.transport) return;

    const transport = data.transport;
    const stops = transport.stops || [];
    const timeline = document.getElementById('timeline');
    const currentBus = transport.current_bus;

    timeline.innerHTML = '';

    // Show only next 8 stops
    const relevantStops = stops.slice(0, 8);

    relevantStops.forEach((stop) => {
        const item = document.createElement('div');
        const isActive = stop.is_next;
        item.className = `timeline-item ${isActive ? 'active' : 'future'}`;

        let etaText;
        if (isActive) {
            etaText = '<div class="eta-badge live">ŞİMDİ</div>';
        } else if (stop.eta === '?') {
            etaText = '<div class="eta-badge">--</div>';
        } else {
            etaText = `<div class="eta-badge">${stop.eta} dk</div>`;
        }

        item.innerHTML = `
            <div class="time">${calculateTime(stop.eta)}</div>
            <div class="dot ${isActive ? 'pulse' : ''}"></div>
            <div class="stop-name">${stop.name}</div>
            ${etaText}
        `;

        timeline.appendChild(item);
    });

    // Show bus info if available
    if (currentBus && currentBus.plate) {
        const busInfo = document.createElement('div');
        busInfo.className = 'bus-info-panel';
        busInfo.innerHTML = `
            <div class="bus-plate">🚌 ${currentBus.plate}</div>
            <div class="bus-stats">
                <span>${currentBus.speed || 0} km/s</span>
                <span>•</span>
                <span>${currentBus.passengers || 0} yolcu</span>
            </div>
        `;
        timeline.insertBefore(busInfo, timeline.firstChild);
    }
}

// Update Weather
function renderWeather(data) {
    // Weather from transport data (data_provider fetches it)
    if (data && data.transport && data.transport.weather) {
        const weather = data.transport.weather;
        document.getElementById('temp').textContent = weather.temp + "°C";
        document.getElementById('weather-desc').textContent = weather.desc;
    }
}

// Update Next Stop Banner
function renderNextStop(data) {
    if (!data || !data.transport) return;

    const transport = data.transport;
    document.getElementById('next-stop-name').textContent = transport.next_stop || "BİLGİ YOK";

    // Update plate in footer if available
    const plateEl = document.querySelector('.bus-plate');
    if (plateEl && transport.current_bus && transport.current_bus.plate) {
        plateEl.textContent = transport.current_bus.plate;
    }
}

// Calculate time from ETA minutes
function calculateTime(addMinutes) {
    if (addMinutes === '?' || addMinutes === undefined) return '--:--';
    const now = new Date();
    now.setMinutes(now.getMinutes() + parseInt(addMinutes || 0));
    return now.toTimeString().substring(0, 5);
}

// Update Clock
function updateClock() {
    const now = new Date();
    document.getElementById('clock').textContent = now.toTimeString().substring(0, 5);
    const options = { day: 'numeric', month: 'long', year: 'numeric' };
    document.getElementById('date').textContent = now.toLocaleDateString('tr-TR', options);
}

// Main Update Function
async function updateScreen() {
    try {
        const response = await fetch(`${API_URL}?line=${LINE_CODE}&stop_seq=${MY_STOP_SEQ}`);
        const data = await response.json();

        if (data.error) {
            console.error("API Error:", data.error);
            return;
        }

        // Update all components
        updateMap(data);
        renderTimeline(data);
        renderWeather(data);
        renderNextStop(data);

    } catch (e) {
        console.error("Fetch error:", e);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', function () {
    initMap();
    updateScreen();
    updateClock();
    loadEvents();  // Load Samsun events
    startMediaRotation();  // Start YouTube/Map rotation

    // Refresh data every 5 seconds (Real-time tracking)
    setInterval(updateScreen, 5000);

    // Clock every second
    setInterval(updateClock, 1000);

    // Auto-rotate events every 8 seconds
    setInterval(() => nextEvent(), 8000);
});

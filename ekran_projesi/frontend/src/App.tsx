import { useState, useEffect } from 'react'
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import type { ScreenData } from './types'
import WeatherWidget from './components/WeatherWidget'
import TransportWidget from './components/TransportWidget'
import EventsWidget from './components/EventsWidget'
import SplitScreen from './layout/SplitScreen'
import L from 'leaflet'

// Fix for default Leaflet marker icons
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

// Custom Bus Icon
const busIcon = new L.DivIcon({
    className: 'custom-bus-icon',
    html: `<div style="background-color: #2563eb; width: 32px; height: 32px; border-radius: 50%; border: 3px solid white; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <polygon points="3 11 22 2 13 21 11 13 3 11"></polygon>
            </svg>
         </div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16]
});

// Component to auto-center map
function MapUpdater({ center }: { center: [number, number] }) {
    const map = useMap();
    useEffect(() => {
        map.flyTo(center, map.getZoom());
    }, [center, map]);
    return null;
}

function App() {
    const [data, setData] = useState<ScreenData | null>(null)

    // Poll API every 3 seconds
    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await fetch('/api/screen-data?line=26/17&stop_seq=10'); // Default test params
                const json: ScreenData = await res.json();
                setData(json);
            } catch (err) {
                console.error("API Error:", err);
            }
        };

        fetchData(); // Initial
        const interval = setInterval(fetchData, 3000); // Poll
        return () => clearInterval(interval);
    }, []);

    if (!data) return <div className="flex h-screen items-center justify-center bg-black text-white">Yükleniyor...</div>;

    // Determine Map Center (Bus location or default Samsun)
    const mapCenter: [number, number] = data.transport.current_bus
        ? [data.transport.current_bus.lat, data.transport.current_bus.lon]
        : [41.2867, 36.33];

    return (
        <SplitScreen
            mapResult={
                <MapContainer center={mapCenter} zoom={14} scrollWheelZoom={false} style={{ height: '100%', width: '100%' }} zoomControl={false}>
                    <TileLayer
                        attribution='&copy; OpenStreetMap'
                        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                    />

                    {/* Bus Marker */}
                    {data.transport.current_bus && (
                        <Marker position={[data.transport.current_bus.lat, data.transport.current_bus.lon]} icon={busIcon}>
                            <Popup>
                                Bus: {data.transport.current_bus.plate} <br /> Speed: {data.transport.current_bus.speed} km/h
                            </Popup>
                        </Marker>
                    )}

                    {/* Stop Markers */}
                    {data.transport.stops.map(stop => (
                        <Marker key={stop.seq} position={[stop.lat, stop.lon]}>
                            <Popup>{stop.name}</Popup>
                        </Marker>
                    ))}

                    <MapUpdater center={mapCenter} />
                </MapContainer>
            }

            weatherWidget={
                <WeatherWidget
                    weather={data.content.weather}
                />
            }

            eventsWidget={
                <EventsWidget events={data.content.events || []} />
            }

            transportWidget={
                <TransportWidget data={data.transport} />
            }
        />
    )
}

export default App

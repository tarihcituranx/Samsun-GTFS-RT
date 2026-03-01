import React from 'react';

interface SplitScreenProps {
    mapResult: React.ReactNode;
    weatherWidget: React.ReactNode;
    transportWidget: React.ReactNode;
    eventsWidget: React.ReactNode;
}

const SplitScreen: React.FC<SplitScreenProps> = ({ mapResult, weatherWidget, transportWidget, eventsWidget }) => {
    return (
        <div className="h-screen w-screen p-4 flex gap-4">
            {/* LEFT PANEL: Map + Widgets (2fr) */}
            <div className="flex-[2] flex flex-col gap-4 min-h-0 relative">

                {/* Map Container with Glassmorphism Border */}
                <div className="flex-1 relative rounded-2xl overflow-hidden border border-white/10 shadow-2xl bg-black/30 backdrop-blur-sm">
                    {/* Map Background */}
                    <div className="absolute inset-0 z-0">
                        {mapResult}
                    </div>

                    {/* Overlay Widgets (Weather & Events) */}
                    <div className="absolute top-4 left-4 z-10 w-96 flex flex-col gap-4 max-h-[92vh]">
                        {weatherWidget}

                        {/* Events Widget Container */}
                        <div className="overflow-hidden rounded-xl border border-white/10 shadow-lg bg-[#1a1a2e]/90 backdrop-blur-md">
                            {eventsWidget}
                        </div>
                    </div>
                </div>

                {/* Feature Icons Bar (Bottom Left) -- Mimicking vehicle-info-bar */}
                <div className="flex justify-around items-center p-3 rounded-xl border border-white/10 bg-gradient-to-br from-blue-600/10 to-blue-900/10 backdrop-blur-md">
                    <div className="flex items-center gap-2 text-gray-400 text-sm"><span className="text-blue-500 text-lg">📶</span> Ücretsiz Wi-Fi</div>
                    <div className="flex items-center gap-2 text-gray-400 text-sm"><span className="text-blue-500 text-lg">🔋</span> USB Şarj</div>
                    <div className="flex items-center gap-2 text-gray-400 text-sm"><span className="text-blue-500 text-lg">❄️</span> Klima: 22°C</div>
                    <div className="flex items-center gap-2 text-gray-400 text-sm"><span className="text-blue-500 text-lg">♿</span> Engelsiz</div>
                </div>
            </div>

            {/* RIGHT PANEL: Timeline (1fr) */}
            <div className="flex-1 flex flex-col rounded-2xl border border-white/10 shadow-2xl bg-gradient-to-br from-[#1a1a2e]/50 to-[#16213e]/50 backdrop-blur-md p-5 overflow-hidden">
                {transportWidget}
            </div>
        </div>
    );
};

export default SplitScreen;

import React from 'react';
import { Cloud, Sun, CloudRain, CloudSnow } from 'lucide-react';
import type { Weather } from '../types';

interface WeatherWidgetProps {
    weather: Weather;
}

const WeatherWidget: React.FC<WeatherWidgetProps> = ({ weather }) => {
    // Simple icon mapping based on description or code
    const getWeatherIcon = (code: string) => {
        const c = code.toUpperCase();
        if (c.includes('GÜNEŞ') || c === 'A') return <Sun className="w-12 h-12 text-yellow-400" />;
        if (c.includes('YAĞMUR') || c.includes('Y')) return <CloudRain className="w-12 h-12 text-blue-400" />;
        if (c.includes('KAR') || c.includes('K')) return <CloudSnow className="w-12 h-12 text-white" />;
        return <Cloud className="w-12 h-12 text-gray-300" />;
    };

    return (
        <div className="flex flex-col bg-white/5 backdrop-blur-md rounded-xl p-5 text-white shadow-lg border border-white/10 transition-all hover:bg-white/10">
            {/* Weather Content */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    {getWeatherIcon(weather.code)}
                    <div>
                        <div className="text-5xl font-bold tracking-tighter">{weather.temp}°</div>
                        <div className="text-lg opacity-80 font-medium">{weather.desc}</div>
                    </div>
                </div>
                <div className="text-right flex flex-col items-end">
                    <h2 className="text-xs uppercase tracking-[0.2em] opacity-60 mb-1">SAMSUN</h2>
                    <div className="px-2 py-1 bg-white/10 rounded text-[10px] text-blue-200">Valilik Verisi</div>
                </div>
            </div>
        </div>
    );
};

export default WeatherWidget;

import React, { useState, useEffect } from 'react';
import type { Event } from '../types';

interface EventsWidgetProps {
    events: Event[];
}

const EventsWidget: React.FC<EventsWidgetProps> = ({ events }) => {
    const [currentIndex, setCurrentIndex] = useState(0);

    // Auto-rotate events
    useEffect(() => {
        if (events.length === 0) return;
        const interval = setInterval(() => {
            setCurrentIndex((prev) => (prev + 1) % events.length);
        }, 8000);
        return () => clearInterval(interval);
    }, [events.length]);

    if (events.length === 0) {
        return <div className="p-4 text-center opacity-50 text-sm">Etkinlik bulunamadı.</div>;
    }

    const event = events[currentIndex];

    // Type color mapping
    const getTypeColor = (type: string) => {
        if (type === 'Tiyatro') return 'text-pink-500';
        if (type === 'Müzik') return 'text-purple-500';
        if (type === 'OperaBale') return 'text-indigo-500';
        return 'text-cyan-400';
    };

    return (
        <div className="p-3 w-full">
            {/* Header */}
            <div className="flex items-center justify-between mb-3 text-white font-bold px-1">
                <span className="flex items-center gap-2">🎭 Bu Hafta Samsun'da</span>
                <div className="flex gap-1">
                    <button
                        onClick={() => setCurrentIndex((prev) => (prev - 1 + events.length) % events.length)}
                        className="w-7 h-7 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                    >‹</button>
                    <button
                        onClick={() => setCurrentIndex((prev) => (prev + 1) % events.length)}
                        className="w-7 h-7 flex items-center justify-center rounded-full bg-white/10 hover:bg-white/20 transition-colors"
                    >›</button>
                </div>
            </div>

            {/* Event Card (Visual) */}
            <div className="flex gap-3 bg-black/30 rounded-lg p-3 min-h-[100px] border-l-4 border-pink-500 animate-fade-in">
                {/* Thumb */}
                <img
                    src={event.image || ''}
                    alt={event.title}
                    className="w-24 h-16 rounded-md object-cover bg-gray-800 shrink-0"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = 'none'; }}
                />

                {/* Details */}
                <div className="flex-1 overflow-hidden flex flex-col justify-center">
                    <div className={`text-[10px] uppercase font-bold tracking-wider mb-1 ${getTypeColor(event.type)}`}>
                        {event.type || 'ETKİNLİK'}
                    </div>
                    <div className="text-white font-medium text-sm leading-tight mb-1 line-clamp-2">
                        {event.title}
                    </div>
                    <div className="flex gap-3 text-xs text-gray-400">
                        <span className="flex items-center gap-1">📍 {event.venue}</span>
                    </div>
                    <div className="flex gap-3 text-xs text-gray-400">
                        <span className="flex items-center gap-1">📅 {event.date}, {event.time}</span>
                    </div>
                </div>
            </div>

            {/* Pagination Dots */}
            <div className="flex justify-center gap-1 mt-3">
                {events.map((_, idx) => (
                    <div
                        key={idx}
                        className={`h-1 rounded-full transition-all duration-300 ${idx === currentIndex ? 'w-4 bg-pink-500' : 'w-1 bg-white/20'}`}
                    />
                ))}
            </div>
        </div>
    );
};

export default EventsWidget;

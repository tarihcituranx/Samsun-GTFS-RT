import React, { useEffect, useRef } from 'react';
import type { TransportData } from '../types';

interface TransportWidgetProps {
    data: TransportData;
}

const TransportWidget: React.FC<TransportWidgetProps> = ({ data }) => {
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll logic if needed
    useEffect(() => {
        if (scrollRef.current) {
            // Logic to keep active stop in view could go here
        }
    }, [data.stops]);

    const activeIndex = data.stops.findIndex(s => s.is_next);

    return (
        <div className="flex flex-col h-full relative">
            {/* Header: Line Badge */}
            <div className="flex flex-col gap-2 mb-4 pb-4 border-b border-white/10">
                <div className="bg-gradient-to-br from-blue-600 to-blue-800 text-white text-3xl font-bold py-3 px-6 rounded-xl text-center shadow-lg shadow-blue-600/30 tracking-widest">
                    {data.line_code}
                </div>
                <div className="text-center text-gray-400 font-medium text-sm">
                    {data.line_name}
                </div>
            </div>

            {/* Timeline */}
            <div className="flex-1 overflow-y-auto pr-2 custom-scrollbar" ref={scrollRef}>
                {data.stops.slice(0, 10).map((stop, i) => { // Limit to 10 for performance/view
                    const isActive = stop.is_next;
                    const isPassed = !isActive && i < activeIndex; // Simplified assumption for frontend demo

                    return (
                        <div key={i} className={`relative grid grid-cols-[50px_20px_1fr_60px] gap-3 items-center py-4 px-2 rounded-lg transition-all
                            ${isActive ? 'bg-gradient-to-r from-transparent via-blue-600/10 to-transparent scale-[1.02] my-2' : ''}
                            ${isPassed ? 'opacity-40' : ''}
                        `}>
                            {/* Vertical Line */}
                            {i !== data.stops.length - 1 && (
                                <div className="absolute left-[79px] top-1/2 bottom-[-50%] w-0.5 bg-white/20 -z-10" />
                            )}

                            {/* Time */}
                            <div className={`text-right font-medium text-sm ${isActive ? 'text-blue-400 font-bold' : 'text-gray-500'}`}>
                                {stop.eta !== '?' ? `+${stop.eta} dk` : '--'}
                            </div>

                            {/* Dot */}
                            <div className="relative flex justify-center">
                                <div className={`w-4 h-4 rounded-full border-[3px] z-10 box-content transition-all duration-500
                                    ${isActive
                                        ? 'bg-blue-600 border-blue-400 shadow-[0_0_15px_rgba(37,99,235,0.6)] scale-125 animate-pulse'
                                        : isPassed ? 'bg-gray-600 border-gray-500' : 'bg-white/20 border-white/10'
                                    }
                                `} />
                            </div>

                            {/* Stop Name */}
                            <div className={`text-base truncate ${isActive ? 'text-white font-bold' : 'text-gray-300'}`}>
                                {stop.name}
                            </div>

                            {/* ETA Badge */}
                            <div className="flex justify-end">
                                {isActive ? (
                                    <span className="bg-green-600 text-white text-xs font-bold px-2 py-1 rounded-full shadow animate-pulse">
                                        ŞİMDİ
                                    </span>
                                ) : stop.eta !== '?' && (
                                    <span className="bg-white/10 text-gray-300 text-xs font-bold px-2 py-1 rounded-full border border-white/5">
                                        {stop.eta} dk
                                    </span>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Footer: Next Stop Banner */}
            <div className="mt-4 bg-gradient-to-r from-pink-600 to-pink-800 rounded-xl p-4 flex items-center justify-between shadow-lg shadow-pink-600/30 border border-white/10">
                <div className="flex flex-col">
                    <span className="text-[10px] font-bold tracking-widest text-white/80">GELECEK DURAK / NEXT STOP</span>
                    <span className="text-xl font-bold text-white tracking-widest uppercase truncate max-w-[200px]">
                        {data.stops.find(s => s.is_next)?.name || 'SON DURAK'}
                    </span>
                </div>
                <div className="bg-white/20 px-3 py-1.5 rounded-lg text-lg font-bold border-2 border-white/30 backdrop-blur-sm">
                    {data.current_bus?.plate || '55 -- ---'}
                </div>
            </div>
        </div>
    );
};

export default TransportWidget;

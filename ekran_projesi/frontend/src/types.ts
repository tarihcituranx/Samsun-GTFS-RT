export interface Weather {
    temp: string;
    desc: string;
    code: string;
}

export interface Bus {
    plate: string;
    lat: number;
    lon: number;
    speed: number;
    heading: number;
    passengers: number;
    closest_stop_seq: number;
}

export interface Stop {
    name: string;
    seq: number;
    lat: number;
    lon: number;
    eta: number | string;
    is_next: boolean;
}

export interface TransportData {
    current_bus: Bus | null;
    stops: Stop[];
    next_stop: string;
    eta: number | null;
    has_live_data: boolean;
    line_code: string;
    line_name: string;
    current_time: string;
    weather: Weather;
}

export interface Event {
    title: string;
    venue: string;
    date: string;
    time: string;
    type: string;
    image: string;
    url: string;
}

export interface ContentData {
    updated_at: string;
    weather: Weather;
    events: Event[];
}

export interface ScreenData {
    transport: TransportData;
    content: ContentData;
    timestamp: string;
}

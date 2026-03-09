# Samsun Transit Pulse - Premium UI/UX Tasarım Promptu (Lovable için)

Aşağıdaki metni kopyalayıp doğrudan Lovable'a (veya benzeri bir AI UI oluşturucuya) yapıştırabilirsin. Bu versiyon çok daha detaylı, modern tasarım trendlerini içeren ve kusursuz bir sonuç almak için optimize edilmiştir:

***

**System Role & Project Goal:**
Act as an expert Frontend Developer and UI/UX Designer. Create a comprehensive, premium "Mobile-First" PWA web application named "Samsun Transit Pulse". 
The app is a real-time public transit tracking application for Samsun, Turkey. It must feature a flawless Dark/Light mode toggle, a modern "Glassmorphism" aesthetic, and highly interactive layouts. 
The background of the entire application should be a full-screen, interactive Leaflet map (or a styled map placeholder). UI elements should float above the map.

**1. Core Aesthetics & Design System (Tailwind CSS):**
- **Color Palette:** 
  - Primary Accent: Vibrant Orange (`#ea580c` to `#f97316`) for active states, CTA buttons, and live indicators.
  - Secondary/Brand Colors: Deep Sea Blue (`#0ea5e9`) for maritime lines (boats) and Forest Green (`#16a34a`) for eco-friendly lines (trams).
  - Backgrounds: Dark Mode (`#0f172a` or `#020617` with heavy transparency), Light Mode (`#ffffff` or `#f8fafc` with transparency).
- **Glassmorphism:** ALL overlaid panels (sidebar, bottom sheet, navigation bars, floating cards) MUST use `backdrop-blur-md` or `backdrop-blur-xl` with semi-transparent background colors (e.g., `bg-slate-900/70` in dark mode) and subtle borders (`border-white/10`).
- **Typography:** Use the `Inter` or `Outfit` font family. Use track-tight headings, bold weights for numbers/times, and highly legible varying text sizes for hierarchy.
- **Animations & Micro-interactions:**
  - Smooth page transitions and layout animations.
  - Hover states for all clickable elements (scale up slightly, brighten color).
  - CSS pulsing animations (e.g., `animate-pulse` or custom radar wave effects) for live vehicle markers and "Live" badges.

**2. Layout Architecture (Responsive):**
- **Mobile (< 768px):** 
  - Floating Top Bar (Search + Actions).
  - Full-screen map underneath.
  - A draggable/swipeable "Bottom Sheet" (Framer Motion style) that snaps to 20%, 50%, and 90% screen heights. This sheet contains the main content.
  - A persistent Bottom Navigation Bar with 5 icons.
- **Desktop (>= 768px):** 
  - The map remains full-screen.
  - The Bottom Sheet converts into a fixed, elegant "Left Sidebar Panel" (approx 400px wide).
  - Sidebar Navigation instead of Bottom Nav.

**3. Main Navigation Models & Views (The 5 Tabs):**
- **🌍 Harita (Map View):** Default view. Shows the map with floating Top Bar. Minimal UI to maximize map visibility.
- **🚌 Hatlar (Lines List):** 
  - A comprehensive list of public transit routes.
  - Include horizontal scrollable category pills: "All", "Otobüs" (Bus), "Tramvay" (Tram), "Ekspres", "Ring", "Teleferik", "Vapur" (Boat), "Samair" (Airport).
  - Line Cards: Each card has the route code (e.g., "E1", "T1") inside a brightly colored rounded square, the route name, and an arrow icon.
- **📍 Yakınım (Near Me):** 
  - Geolocation-based view. Shows nearest stops.
  - Stop Cards: Stop name, distance (e.g., "120m"), and a horizontal scrolling list of buses arriving soon with countdown badges (e.g., "E1: 2 min", "19: 5 min").
- **🧭 Rota (Route Planner):** 
  - "From" and "To" input fields with swap button.
  - Time selector (Leave now vs. Arrive by).
  - Step-by-step visual timeline of the proposed trip (Walk icon -> Wait icon -> Bus icon -> Walk icon).
- **📸 Keşfet (Discover Samsun):** 
  - Tourist guide section.
  - Masonry or grid layout of beautiful image cards for places like "Bandırma Vapuru", "Amazon Köyü", "Amisos Tepesi".

**4. Deep-Dive Component Specifications:**
When a Line is clicked, the UI transitions to the **Line Detail View**:
- **Header:** Sticky top, showing the Line Code prominently, Line Name, and a "Direction" toggle switch (e.g., "Ondokuz Mayıs Üni. ⇄ Tekkeköy").
- **Quick Stats Grid:** 3 elegant cards showing "Stops" (e.g., 42), "Active Vehicles" (e.g., 8), and "Fare" (e.g., ₺24.00).
- **Live Vehicles List:** A section showing vehicles currently on route. Include plate number, current speed, and a pulsing green dot.
- **Interactive Stop Timeline:** A vertical timeline (like a transit map). Passed stops are dimmed, upcoming stops are bright. Highlight the stops where live vehicles are currently located.

**5. Custom Map Markers (HTML/CSS Overlays):**
- **Vehicle Marker:** A dynamic marker. For example, a rounded pin containing the vehicle's line code, surrounded by an animated expanding ring (radar effect).
- **Stop Marker:** Small, elegant glassmorphic circles. When clicked, it opens a small popup showing the next 3 arrivals.

**6. Technical Implementation Rules for the AI:**
- Build this as a single-page React application using Tailwind CSS.
- **DO NOT** leave placeholders or write "Here you would fetch data". You MUST mock all data using detailed, realistic JSON arrays embedded in the code so the prototype looks fully alive. Mock at least 5 lines, 10 stops, and some live vehicles.
- Implement the Dark/Light mode toggle fully using Tailwind's `dark:` classes and React state.
- Ensure the UI feels like a premium native iOS/Android application. Use `overflow-y-auto` with hidden scrollbars for content lists.
- Add an "Info Modal" triggered from the Top Bar for "Aktarma Kuralları" (Transfer Rules) showing a neat table of discount rates.

**Output Request:**
Generate the complete, fully functional, and visually breathtaking code for this React application. Prioritize polished CSS, fluid layouts, and an immediate "Wow" factor upon first load.
***

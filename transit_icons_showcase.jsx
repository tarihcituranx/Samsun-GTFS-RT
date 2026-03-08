import { useState } from "react";

const icons = [
  {
    id: "bus",
    label: "Otobüs",
    category: "kara",
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="20" height="14" rx="2"/>
      <path d="M2 9h20"/>
      <circle cx="7" cy="19" r="1.5"/>
      <circle cx="17" cy="19" r="1.5"/>
      <path d="M7 17.5v1M17 17.5v1"/>
      <path d="M2 13h1M21 13h1"/>
      <path d="M7 9v5M12 9v5M17 9v5"/>
    </svg>`,
    material: "directions_bus",
    phosphor: "Bus",
    color: "#3b82f6",
  },
  {
    id: "tram",
    label: "Tramvay",
    category: "kara",
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="5" width="16" height="14" rx="2"/>
      <path d="M4 10h16"/>
      <path d="M8 5V3M16 5V3"/>
      <path d="M3 3h18"/>
      <circle cx="8.5" cy="17" r="1.2"/>
      <circle cx="15.5" cy="17" r="1.2"/>
      <path d="M6 21l2-2.5M18 21l-2-2.5"/>
      <path d="M8 10v5M12 10v5M16 10v5"/>
    </svg>`,
    material: "tram",
    phosphor: "Tram",
    color: "#10b981",
  },
  {
    id: "metro",
    label: "Metro",
    category: "kara",
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <rect x="3" y="3" width="18" height="14" rx="3"/>
      <circle cx="8.5" cy="17.5" r="1.5"/>
      <circle cx="15.5" cy="17.5" r="1.5"/>
      <path d="M8.5 16V19M15.5 16V19"/>
      <path d="M10 19h4"/>
      <path d="M7 9l2.5 4L12 7l2.5 4L17 9"/>
    </svg>`,
    material: "subway",
    phosphor: "Train",
    color: "#8b5cf6",
  },
  {
    id: "airport_shuttle",
    label: "Havalimanı Servisi",
    category: "kara",
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M3 12h13l4-4H3"/>
      <path d="M3 16h13l4-4"/>
      <circle cx="7" cy="19" r="1.5"/>
      <circle cx="15" cy="19" r="1.5"/>
      <path d="M20 8l-2-3"/>
      <path d="M17 8h3"/>
    </svg>`,
    material: "airport_shuttle",
    phosphor: "Van",
    color: "#f59e0b",
  },
  {
    id: "minibus",
    label: "Minibüs",
    category: "kara",
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M1 10l2-5h14l4 5v6H1z"/>
      <path d="M1 10h19"/>
      <circle cx="6" cy="18" r="1.5"/>
      <circle cx="16" cy="18" r="1.5"/>
      <path d="M6 16.5V19M16 16.5V19"/>
      <rect x="4" y="11" width="4" height="3" rx="0.5"/>
      <rect x="10" y="11" width="4" height="3" rx="0.5"/>
    </svg>`,
    material: "directions_bus",
    phosphor: "Bus",
    color: "#ef4444",
  },
  {
    id: "ferry",
    label: "Feribot",
    category: "deniz",
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M3 17l1.5-7h15l1.5 7"/>
      <path d="M2 20c1.5-2 3-2 4.5 0s3 2 4.5 0 3 2 4.5 0 3-2 4.5 0"/>
      <rect x="7" y="7" width="10" height="3" rx="1"/>
      <path d="M12 7V4M9 4h6"/>
      <path d="M5 10h14"/>
    </svg>`,
    material: "directions_ferry",
    phosphor: "Boat",
    color: "#0ea5e9",
  },
  {
    id: "speedboat",
    label: "Deniz Otobüsü",
    category: "deniz",
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M2 17c4-4 8-4 12-1l6-5"/>
      <path d="M14 16l2-8 4 3"/>
      <path d="M2 20c1.5-2 3-2 4.5 0s3 2 4.5 0 3 2 4.5 0 3-2 4.5 0"/>
      <circle cx="18" cy="8" r="1"/>
    </svg>`,
    material: "sailing",
    phosphor: "Boat",
    color: "#06b6d4",
  },
  {
    id: "airplane",
    label: "Uçak",
    category: "hava",
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 16l-4-8-4 4H3l2 2h4l-2 4h3l2-2h4l2 2h3z"/>
    </svg>`,
    material: "flight",
    phosphor: "Airplane",
    color: "#6366f1",
  },
  {
    id: "cable_car",
    label: "Teleferik / Füniküler",
    category: "özel",
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <path d="M2 6l20-2"/>
      <path d="M7 6l-1 2h12l-1-2"/>
      <rect x="6" y="8" width="12" height="8" rx="2"/>
      <path d="M9 8v8M15 8v8"/>
      <circle cx="12" cy="5.5" r="1"/>
    </svg>`,
    material: "cable_car",
    phosphor: "GondolaLift",
    color: "#ec4899",
  },
  {
    id: "bike",
    label: "Bisiklet",
    category: "özel",
    svg: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="5.5" cy="17.5" r="3.5"/>
      <circle cx="18.5" cy="17.5" r="3.5"/>
      <path d="M15 6h-3l-3 11.5M12 6l3 5.5H5.5"/>
      <circle cx="15" cy="5" r="1"/>
    </svg>`,
    material: "pedal_bike",
    phosphor: "Bicycle",
    color: "#84cc16",
  },
];

const categories = ["tümü", "kara", "deniz", "hava", "özel"];

const libraries = [
  {
    name: "Material Symbols",
    url: "https://fonts.google.com/icons",
    flutter: "Icons.directions_bus",
    web: "<span class='material-symbols-rounded'>directions_bus</span>",
    note: "Flutter'da hazır gelir, web için CDN var",
    tag: "ÜCRETSİZ",
    tagColor: "#10b981",
  },
  {
    name: "Phosphor Icons",
    url: "https://phosphoricons.com",
    flutter: "phosphor_flutter paketi",
    web: "phosphor-icons npm",
    note: "Çok stil: thin, light, regular, bold, fill, duotone",
    tag: "ÜCRETSİZ",
    tagColor: "#10b981",
  },
  {
    name: "Lucide Icons",
    url: "https://lucide.dev",
    flutter: "lucide_flutter paketi",
    web: "lucide-react / lucide npm",
    note: "Temiz SVG, currentColor destekli",
    tag: "ÜCRETSİZ",
    tagColor: "#10b981",
  },
  {
    name: "Font Awesome",
    url: "https://fontawesome.com",
    flutter: "font_awesome_flutter",
    web: "FA CDN / npm",
    note: "Pro'da daha fazla transit ikonu var",
    tag: "FREEMIUM",
    tagColor: "#f59e0b",
  },
  {
    name: "Flaticon / Freepik",
    url: "https://flaticon.com",
    flutter: "SVG olarak indir, flutter_svg ile kullan",
    web: "SVG embed",
    note: "Özel tasarım transit SVG setleri mevcut",
    tag: "FREEMIUM",
    tagColor: "#f59e0b",
  },
  {
    name: "SVGRepo",
    url: "https://svgrepo.com",
    flutter: "flutter_svg paketi",
    web: "Inline SVG",
    note: "500k+ ücretsiz SVG, arama: 'bus', 'ferry', 'tram'",
    tag: "ÜCRETSİZ",
    tagColor: "#10b981",
  },
];

export default function IconShowcase() {
  const [dark, setDark] = useState(true);
  const [category, setCategory] = useState("tümü");
  const [size, setSize] = useState(40);
  const [style, setStyle] = useState("outline");
  const [selected, setSelected] = useState(null);

  const bg = dark ? "#0a0f1a" : "#f1f5f9";
  const surface = dark ? "#111827" : "#ffffff";
  const surface2 = dark ? "#1e293b" : "#f8fafc";
  const border = dark ? "#1e293b" : "#e2e8f0";
  const text = dark ? "#f1f5f9" : "#0f172a";
  const text2 = dark ? "#94a3b8" : "#64748b";

  const filtered = icons.filter(i => category === "tümü" || i.category === category);

  return (
    <div style={{ background: bg, minHeight: "100vh", fontFamily: "'Inter', system-ui, sans-serif", color: text, transition: "all 0.3s" }}>
      {/* Header */}
      <div style={{ background: surface, borderBottom: `1px solid ${border}`, padding: "20px 28px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontWeight: "800", fontSize: "18px" }}>🚌 Transit İkon Seti</div>
          <div style={{ fontSize: "12px", color: text2, marginTop: "2px" }}>Ulaşım uygulamaları için tema uyumlu ikonlar</div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span style={{ fontSize: "13px", color: text2 }}>{dark ? "🌙 Karanlık" : "☀️ Aydınlık"}</span>
          <div
            onClick={() => setDark(!dark)}
            style={{
              width: "52px", height: "28px",
              background: dark ? "#3b82f6" : "#e2e8f0",
              borderRadius: "999px",
              cursor: "pointer",
              position: "relative",
              transition: "background 0.3s",
            }}
          >
            <div style={{
              position: "absolute",
              top: "4px",
              left: dark ? "28px" : "4px",
              width: "20px", height: "20px",
              background: "#fff",
              borderRadius: "50%",
              transition: "left 0.3s",
              boxShadow: "0 1px 4px rgba(0,0,0,0.3)",
            }}/>
          </div>
        </div>
      </div>

      <div style={{ padding: "24px 28px" }}>
        {/* Controls */}
        <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", marginBottom: "24px", alignItems: "center" }}>
          <div style={{ display: "flex", gap: "6px" }}>
            {categories.map(c => (
              <button key={c} onClick={() => setCategory(c)} style={{
                background: category === c ? "#3b82f6" : surface,
                color: category === c ? "#fff" : text2,
                border: `1px solid ${category === c ? "#3b82f6" : border}`,
                borderRadius: "999px",
                padding: "6px 14px",
                fontSize: "12px",
                cursor: "pointer",
                fontFamily: "inherit",
                textTransform: "capitalize",
              }}>{c === "tümü" ? "Tümü" : c.charAt(0).toUpperCase() + c.slice(1)}</button>
            ))}
          </div>
          <div style={{ display: "flex", gap: "6px", marginLeft: "auto" }}>
            {["outline", "filled"].map(s => (
              <button key={s} onClick={() => setStyle(s)} style={{
                background: style === s ? surface2 : "transparent",
                color: style === s ? text : text2,
                border: `1px solid ${style === s ? border : "transparent"}`,
                borderRadius: "8px",
                padding: "6px 12px",
                fontSize: "12px",
                cursor: "pointer",
                fontFamily: "inherit",
              }}>{s === "outline" ? "⭕ Outline" : "⬛ Filled"}</button>
            ))}
            <input type="range" min="24" max="72" value={size} onChange={e => setSize(+e.target.value)}
              style={{ width: "80px", accentColor: "#3b82f6" }}/>
            <span style={{ fontSize: "12px", color: text2, minWidth: "35px" }}>{size}px</span>
          </div>
        </div>

        {/* Icon Grid */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(130px, 1fr))", gap: "12px", marginBottom: "32px" }}>
          {filtered.map(icon => (
            <div
              key={icon.id}
              onClick={() => setSelected(selected?.id === icon.id ? null : icon)}
              style={{
                background: selected?.id === icon.id ? (dark ? "#1e3a5f" : "#dbeafe") : surface,
                border: `2px solid ${selected?.id === icon.id ? "#3b82f6" : border}`,
                borderRadius: "16px",
                padding: "20px 12px",
                textAlign: "center",
                cursor: "pointer",
                transition: "all 0.2s",
              }}
            >
              <div style={{
                width: size, height: size,
                margin: "0 auto 10px",
                color: style === "filled" ? icon.color : (dark ? "#e2e8f0" : "#334155"),
              }}
                dangerouslySetInnerHTML={{ __html: icon.svg.replace(
                  /stroke="currentColor"/,
                  style === "filled" ? `stroke="none" fill="${icon.color}"` : 'stroke="currentColor"'
                )}}
              />
              <div style={{ fontSize: "12px", fontWeight: "600", color: text }}>{icon.label}</div>
              <div style={{
                fontSize: "10px",
                marginTop: "4px",
                padding: "2px 8px",
                borderRadius: "999px",
                display: "inline-block",
                background: icon.color + "22",
                color: icon.color,
              }}>{icon.category}</div>
            </div>
          ))}
        </div>

        {/* Selected Icon Detail */}
        {selected && (
          <div style={{
            background: surface,
            border: `1px solid ${border}`,
            borderRadius: "16px",
            padding: "24px",
            marginBottom: "32px",
          }}>
            <div style={{ fontWeight: "700", marginBottom: "16px", fontSize: "15px" }}>
              📌 {selected.label} — Kullanım Kodu
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
              {[
                {
                  title: "Flutter (flutter_svg)",
                  code: `SvgPicture.asset(\n  'assets/icons/${selected.id}.svg',\n  colorFilter: ColorFilter.mode(\n    Theme.of(context).iconTheme.color!,\n    BlendMode.srcIn,\n  ),\n  width: 24, height: 24,\n)`,
                },
                {
                  title: "Flutter (Material Icons)",
                  code: `Icon(\n  Icons.${selected.material},\n  color: Theme.of(context).iconTheme.color,\n  size: 24,\n)`,
                },
                {
                  title: "Web (Inline SVG)",
                  code: `<svg width="24" height="24"\n  style="color: currentColor"\n  ...>\n  <!-- currentColor tema rengini takip eder -->\n</svg>`,
                },
                {
                  title: "Web (CSS dark mode)",
                  code: `.icon {\n  color: #1e293b; /* light */\n}\n@media (prefers-color-scheme: dark) {\n  .icon {\n    color: #f1f5f9; /* dark */\n  }\n}`,
                },
              ].map(({ title, code }) => (
                <div key={title} style={{ background: dark ? "#0a0f1a" : "#f8fafc", borderRadius: "10px", padding: "14px" }}>
                  <div style={{ fontSize: "11px", color: text2, marginBottom: "8px", fontWeight: "600" }}>{title}</div>
                  <pre style={{ margin: 0, fontSize: "11px", color: "#60a5fa", overflow: "auto", fontFamily: "monospace" }}>{code}</pre>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Libraries */}
        <div style={{ marginBottom: "24px" }}>
          <div style={{ fontWeight: "700", fontSize: "15px", marginBottom: "16px" }}>📚 İkon Kütüphaneleri</div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "12px" }}>
            {libraries.map(lib => (
              <div key={lib.name} style={{
                background: surface,
                border: `1px solid ${border}`,
                borderRadius: "12px",
                padding: "16px",
              }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
                  <span style={{ fontWeight: "700", fontSize: "14px" }}>{lib.name}</span>
                  <span style={{
                    fontSize: "10px", padding: "2px 7px", borderRadius: "999px",
                    background: lib.tagColor + "22", color: lib.tagColor, fontWeight: "700",
                  }}>{lib.tag}</span>
                </div>
                <div style={{ fontSize: "12px", color: text2, marginBottom: "8px" }}>{lib.note}</div>
                <div style={{ fontSize: "11px", background: dark ? "#0a0f1a" : "#f1f5f9", borderRadius: "6px", padding: "8px", fontFamily: "monospace" }}>
                  <span style={{ color: "#94a3b8" }}>Flutter: </span>
                  <span style={{ color: "#60a5fa" }}>{lib.flutter}</span>
                </div>
                <a href={lib.url} target="_blank" rel="noopener" style={{
                  display: "inline-block",
                  marginTop: "10px",
                  fontSize: "11px",
                  color: "#3b82f6",
                  textDecoration: "none",
                  border: "1px solid #3b82f633",
                  padding: "4px 10px",
                  borderRadius: "6px",
                }}>🔗 {lib.url.replace("https://", "")}</a>
              </div>
            ))}
          </div>
        </div>

        {/* Flutter Theme Integration */}
        <div style={{ background: surface, border: `1px solid ${border}`, borderRadius: "16px", padding: "24px" }}>
          <div style={{ fontWeight: "700", fontSize: "15px", marginBottom: "16px" }}>⚡ Flutter Tema Entegrasyonu</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
            <div style={{ background: dark ? "#0a0f1a" : "#f8fafc", borderRadius: "10px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: text2, marginBottom: "8px", fontWeight: "600" }}>pubspec.yaml</div>
              <pre style={{ margin: 0, fontSize: "11px", color: "#60a5fa", fontFamily: "monospace" }}>{`dependencies:
  flutter_svg: ^2.0.0
  phosphor_flutter: ^2.1.0
  # veya
  font_awesome_flutter: ^10.7.0

flutter:
  assets:
    - assets/icons/`}</pre>
            </div>
            <div style={{ background: dark ? "#0a0f1a" : "#f8fafc", borderRadius: "10px", padding: "14px" }}>
              <div style={{ fontSize: "11px", color: text2, marginBottom: "8px", fontWeight: "600" }}>ThemeData'da ikonlar</div>
              <pre style={{ margin: 0, fontSize: "11px", color: "#60a5fa", fontFamily: "monospace" }}>{`ThemeData(
  iconTheme: IconThemeData(
    color: Colors.black87,  // light
    size: 24,
  ),
  // dark mode
  darkTheme: ThemeData.dark().copyWith(
    iconTheme: IconThemeData(
      color: Colors.white,
    ),
  ),
)`}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

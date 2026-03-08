import sys

html_top = """<!DOCTYPE html>
<html lang="tr" data-theme="dark">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
    <title>Samsun Transit — Canlı Toplu Taşıma Takibi</title>
    <meta name="description" content="Samsun toplu taşıma araçlarını canlı takip edin. Otobüs, tramvay, tekne, teleferik hatları, sefer saatleri ve durak bilgileri.">
    <meta name="author" content="Samsun Transit" />
    
    <meta property="og:type" content="website" />
    <meta property="og:title" content="Samsun Transit — Canlı Toplu Taşıma Takibi">
    <meta property="og:description" content="Samsun toplu taşıma araçlarını canlı takip edin. Otobüs, tramvay, tekne, teleferik hatları, sefer saatleri ve durak bilgileri.">
    <meta property="og:image" content="https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/b33a06ef-3bbb-4075-86ee-3e764c7781a9/id-preview-416cc31b--667074a0-f4e7-4cb4-9c0c-dfe85c31cdd8.lovable.app-1772983126123.png">
    
    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="Samsun Transit — Canlı Toplu Taşıma Takibi">
    <meta name="twitter:description" content="Samsun toplu taşıma araçlarını canlı takip edin. Otobüs, tramvay, tekne, teleferik hatları, sefer saatleri ve durak bilgileri.">
    <meta name="twitter:image" content="https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/b33a06ef-3bbb-4075-86ee-3e764c7781a9/id-preview-416cc31b--667074a0-f4e7-4cb4-9c0c-dfe85c31cdd8.lovable.app-1772983126123.png">

<script src="https://cdn.tailwindcss.com"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/leaflet.css"/>
<style>
  :root {
      --bg: #ffffff;
      --bg-panel: rgba(255, 255, 255, 0.95);
      --bg-card: #f8fafc;
      --bg-hover: #f1f5f9;
      --border: #e2e8f0;
      --text: #0f172a;
      --text-muted: #64748b;
      --accent: #ea580c;
      --accent-bg: rgba(234, 88, 12, 0.1);
      --nav-bg: rgba(255, 255, 255, 0.98);
  }
  [data-theme="dark"] {
      --bg: #0a0e17;
      --bg-panel: rgba(15, 23, 42, 0.85);
      --bg-card: #1e293b;
      --bg-hover: #334155;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #ea580c;
      --accent-bg: rgba(234, 88, 12, 0.15);
      --nav-bg: rgba(15, 23, 42, 0.92);
  }
  
  body {
      font-family: 'Inter', sans-serif; margin: 0; padding: 0;
      background-color: var(--bg); color: var(--text); overflow: hidden;
  }
  
  #map { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 1; }

  .top-bar {
      position: fixed; top: 0; left: 0; width: 100%; height: 72px; z-index: 40;
      background: linear-gradient(to bottom, rgba(15,23,42,0.95) 0%, rgba(15,23,42,0) 100%);
      display: flex; align-items: center; justify-content: space-between;
      padding: 0 16px; pointer-events: none;
  }

  .pnl {
      position: fixed; z-index: 40; background: var(--bg-panel);
      backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
      border: 1px solid var(--border); display: flex; flex-direction: column;
      transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s;
  }

  @media (min-width: 768px) {
      .pnl {
          top: 80px; left: 24px; bottom: 24px; width: 420px;
          border-radius: 24px; box-shadow: 0 10px 40px rgba(0,0,0,0.3);
      }
      .drag-handle { display: none; }
      body:not(.panel-open) .pnl { transform: translateX(-120%); opacity: 0; pointer-events: none; }
  }

  @media (max-width: 767px) {
      .pnl {
          bottom: 72px; left: 0; width: 100%; border-radius: 28px 28px 0 0;
          height: 75vh; box-shadow: 0 -10px 30px rgba(0,0,0,0.25);
          border-bottom: none; border-left: none; border-right: none;
      }
      .drag-handle { width: 48px; height: 5px; background: var(--border); border-radius: 4px; margin: 14px auto; }
      body:not(.panel-open) .pnl { transform: translateY(100%); opacity: 0; pointer-events: none; }
  }

  .pnl-body { flex: 1; overflow-y: auto; padding: 0 20px 20px; scrollbar-width: none; }
  .pnl-body::-webkit-scrollbar { display: none; }

  .bottom-nav {
      position: fixed; bottom: 0; left: 0; width: 100%; height: 72px; z-index: 50;
      background: var(--nav-bg); backdrop-filter: blur(24px); border-top: 1px solid var(--border);
      display: flex; justify-content: space-around; align-items: center; padding-bottom: env(safe-area-inset-bottom);
  }
  @media (min-width: 768px) {
      .bottom-nav {
          top: 24px; right: 24px; bottom: auto; left: auto; width: auto; height: 52px;
          border-radius: 26px; border: 1px solid var(--border); gap: 8px; padding: 0 12px;
          box-shadow: 0 8px 32px rgba(0,0,0,0.25); background: var(--bg-panel);
      }
  }

  .tab {
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      color: var(--text-muted); font-size: 10px; font-weight: 700; cursor: pointer;
      padding: 8px 16px; border-radius: 16px; transition: all 0.2s;
  }
  @media (min-width: 768px) { .tab { flex-direction: row; gap: 8px; font-size: 13px; } }
  .tab:hover { color: var(--text); background: var(--bg-hover); }
  .tab.on { color: var(--accent); }
  .tab svg { width: 24px; height: 24px; margin-bottom: 4px; stroke-width: 2.5; }
  @media (min-width: 768px) { .tab svg { margin-bottom: 0; width: 20px; height: 20px; } }

  .loading { text-align: center; padding: 40px 0; color: var(--text-muted); font-weight: 600; font-size: 14px; }
  .no-data { text-align: center; padding: 40px 0; color: var(--text-muted); font-size: 14px; font-weight: 500; }
  
  .src-wrap { position: relative; margin: 16px 0; }
  .src-wrap svg { position: absolute; left: 14px; top: 14px; width: 20px; height: 20px; color: var(--text-muted); }
  .src { width: 100%; padding: 14px 16px 14px 44px; background: var(--bg-hover); color: var(--text); border: 1px solid var(--border); border-radius: 16px; outline: none; transition: 0.2s; font-size: 15px; font-weight: 500;}
  .src:focus { border-color: var(--accent); background: var(--bg-card); box-shadow: 0 0 0 4px var(--accent-bg); }

  .sec { font-size: 12px; font-weight: 800; color: var(--text-muted); margin: 24px 0 12px 4px; text-transform: uppercase; letter-spacing: 0.5px; }
  .lst { display: flex; flex-direction: column; gap: 10px; }

  .pulse-it {
      background: var(--bg-card); border: 1px solid var(--border); border-radius: 20px;
      display: flex; align-items: center; padding: 14px 18px; gap: 16px; cursor: pointer; transition: 0.2s;
      box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  }
  .pulse-it:hover { background: var(--bg-hover); transform: translateY(-2px); border-color: var(--border); opacity: 0.9; box-shadow: 0 8px 20px rgba(0,0,0,0.1); }
  
  .it-badge { width: 48px; height: 48px; border-radius: 14px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 800; font-size: 15px; flex-shrink: 0; letter-spacing: -0.5px; }
  .it-info { flex: 1; overflow: hidden; }
  .it-title { font-weight: 700; color: var(--text); font-size: 16px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .it-sub { font-size: 12px; margin-top: 4px; font-weight: 600; display: flex; align-items: center; gap: 6px; }
  .badge-icon-s { width: 14px; height: 14px; display: inline-flex; }
  .badge-icon-s svg { width: 100%; height: 100%; stroke-width: 2.5; }
  .it-arrow { width: 20px; height: 20px; color: var(--text-muted); flex-shrink: 0; opacity: 0.5; }

  .kg { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }
  .kb { background: var(--bg-card); border: 1px solid var(--border); border-radius: 14px; padding: 12px 18px; font-size: 13px; font-weight: 700; color: var(--text); display: flex; align-items: center; gap: 8px; cursor: pointer; transition: 0.2s; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
  .kb:hover { background: var(--bg-hover); transform: translateY(-1px); }
  .kb.on { background: var(--accent-bg); color: var(--accent); border-color: var(--accent); }
  .kb .i { width: 20px; height: 20px; display: flex; }
  .kb .i svg { width: 100%; height: 100%; stroke-width: 2.5; }

  .pulse-marker-wrapper { display: flex; justify-content: center; align-items: center; overflow: visible !important; }
  .pulse-marker { display: flex; align-items: center; gap: 6px; padding: 6px 10px; border-radius: 20px; color: white; border: 2.5px solid white; box-shadow: 0 6px 16px rgba(0,0,0,0.4); z-index: 2; position: relative; }
  .pulse-text { font-size: 13px; font-weight: 800; letter-spacing: -0.2px; }
  .pulse-ring { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: calc(100% + 12px); height: calc(100% + 12px); border-radius: 24px; border: 3px solid; animation: pulsate 2s infinite cubic-bezier(0.0, 0, 0.2, 1); opacity: 0; pointer-events: none; }
  @keyframes pulsate { 0% { opacity: 0.8; transform: translate(-50%, -50%) scale(0.8); } 100% { opacity: 0; transform: translate(-50%, -50%) scale(1.3); } }
  
  .bk { background: var(--bg-hover); color: var(--text); border: 1px solid var(--border); border-radius: 14px; padding: 14px; font-weight: 700; width: 100%; text-align: center; cursor: pointer; transition: 0.2s; margin-bottom: 12px; font-size: 15px; box-shadow: 0 2px 6px rgba(0,0,0,0.05); }
  .bk:hover { background: var(--border); transform: translateY(-1px); }
  
  .drk { display: flex; align-items: center; gap: 14px; padding: 14px 6px; border-bottom: 1px solid var(--border); cursor: pointer; transition: 0.2s; }
  .drk:last-child { border-bottom: none; }
  .drk:hover { background: var(--bg-hover); border-radius: 12px; padding-left: 12px; }
  .drk .no { width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center; justify-content: center; background: var(--bg-hover); color: white; font-weight: 800; font-size: 13px; flex-shrink: 0; text-shadow: 0 1px 2px rgba(0,0,0,0.3); }
  .drk .inf { display: flex; flex-direction: column; }
  .drk .ad { font-weight: 700; color: var(--text); font-size: 15px; line-height: 1.3;}
  .drk .fyt { font-size: 12px; color: var(--text-muted); margin-top: 4px; font-weight: 600; }

  .arac { background: var(--bg-card); border: 1px solid var(--border); border-radius: 20px; padding: 18px; margin-bottom: 10px; cursor: pointer; transition: 0.2s; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
  .arac:hover { border-color: var(--accent); transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.1); }
  .arac .pl { font-size: 16px; font-weight: 800; color: var(--text); display: flex; align-items: center; gap: 8px;}
  
  .ig { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px; }
  .ic { background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 14px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
  .ic .v { font-size: 22px; font-weight: 800; color: var(--text); }
  .ic .l { font-size: 11px; color: var(--text-muted); font-weight: 700; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
  
  .fiyat { background: var(--accent-bg); border: 1px solid var(--accent); border-radius: 20px; padding: 20px; text-align: center; margin-bottom: 20px; color: var(--text); box-shadow: 0 8px 20px rgba(0,0,0,0.05); }
  .fiyat .t { font-size: 12px; font-weight: 800; color: var(--accent); text-transform: uppercase; letter-spacing: 1px; }
  .fiyat .pv { font-size: 40px; font-weight: 800; margin: 8px 0; letter-spacing: -1px; }
  .fiyat .s { font-size: 13px; font-weight: 600; opacity: 0.9; }
  
  .live-badge { display: inline-block; background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 10px; padding: 8px 12px; font-size: 13px; font-weight: 800; margin-top: 10px; }
  .saat { background: var(--bg-card); border-radius: 20px; border: 1px solid var(--border); padding: 18px; margin-bottom: 16px; }
  .saat .t { font-size: 14px; font-weight: 800; color: var(--text); margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
  .saat .t::before { content: "📅"; font-size: 18px; }
  .saattab { display: flex; background: var(--bg-hover); border-radius: 12px; padding: 6px; margin-bottom: 16px; }
  .saattab div { flex: 1; text-align: center; padding: 10px; font-size: 13px; font-weight: 700; color: var(--text-muted); cursor: pointer; border-radius: 8px; transition: 0.2s; }
  .saattab div.on { background: var(--bg-panel); color: var(--text); box-shadow: 0 4px 12px rgba(0,0,0,0.1); border: 1px solid var(--border); }
  .saatlar { display: grid; grid-template-columns: repeat(auto-fill, minmax(65px, 1fr)); gap: 8px; }
  .saatlar span { background: var(--bg-hover); padding: 8px; border-radius: 10px; text-align: center; font-size: 13px; font-weight: 700; color: var(--text); border: 1px solid var(--border); }
  
  .sfr { background: var(--bg-card); border: 1px solid var(--border); border-left: 4px solid var(--accent); padding: 14px; border-radius: 16px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
  .sfr .st { font-weight: 800; color: var(--text); font-size: 15px; }
  .sfr .fr { font-weight: 600; color: var(--text-muted); font-size: 13px; }
  
  .toast { visibility: hidden; position: fixed; left: 50%; bottom: 120px; transform: translateX(-50%); background: var(--text); color: var(--bg); padding: 14px 28px; border-radius: 100px; font-weight: 700; font-size: 14px; z-index: 9999; box-shadow: 0 12px 24px rgba(0,0,0,0.3); transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1); opacity: 0; }
  .toast.show { visibility: visible; bottom: 140px; opacity: 1; }
  
  .modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); z-index: 99999; align-items: center; justify-content: center; padding: 24px; }
  .modal-content { background: var(--bg-panel); border: 1px solid var(--border); border-radius: 28px; width: 100%; max-width: 460px; padding: 28px; box-shadow: 0 24px 60px rgba(0,0,0,0.5); max-height: 85vh; overflow-y: auto; }
</style>
</head>
<body class="panel-open">

<div id="map"></div>

<div class="top-bar">
    <div style="display:flex;align-items:center;gap:12px;pointer-events:auto;background:rgba(15,23,42,0.6);padding:6px 16px 6px 6px;border-radius:20px;border:1px solid rgba(255,255,255,0.1);backdrop-filter:blur(12px);">
        <div style="width:36px;height:36px;background:#ea580c;border-radius:14px;display:flex;align-items:center;justify-content:center;font-weight:800;color:#fff;font-size:16px;">ST</div>
        <div style="display:flex;flex-direction:column;">
            <span style="font-weight:800;font-size:14px;color:#fff;letter-spacing:0.5px">SAMSUN TRANSIT</span>
            <span style="font-weight:700;font-size:10px;color:#94a3b8;letter-spacing:0.5px">CANLI TAKİP</span>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:10px;pointer-events:auto;">
        <div id="weatherWidget" style="background:rgba(15,23,42,0.6);color:#fff;padding:8px 14px;border-radius:20px;font-size:13px;font-weight:800;display:flex;align-items:center;backdrop-filter:blur(12px);border:1px solid rgba(255,255,255,0.1)">⏳</div>
        <div style="background:rgba(16,185,129,0.2);border:1px solid #10b981;color:#10b981;font-weight:800;font-size:12px;padding:8px 14px;border-radius:20px;display:flex;align-items:center;gap:8px;backdrop-filter:blur(12px)"><span style="width:8px;height:8px;background:#10b981;border-radius:50%;display:inline-block;animation:pulsate 2s infinite"></span> CANLI</div>
        <button id="themeToggle" onclick="toggleTheme()" style="width:40px;height:40px;border-radius:50%;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.1);color:#fff;display:flex;align-items:center;justify-content:center;cursor:pointer;backdrop-filter:blur(12px);font-size:16px">🌙</button>
    </div>
</div>

<div class="pnl" id="main-panel">
    <div class="drag-handle"></div>
    <div class="pnl-body" id="ct">
        <div class="loading">⏳ Yükleniyor...</div>
    </div>
</div>

<div class="bottom-nav">
    <div class="tab" data-t="harita">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/></svg>
        <span>Harita</span>
    </div>
    <div class="tab on" data-t="hat">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
        <span>Hatlar</span>
    </div>
    <div class="tab" data-t="rota">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 11 22 2 13 21 11 13 3 11"/></svg>
        <span>Rota</span>
    </div>
    <div class="tab" data-t="yakin">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M2 9h20M7 17.5v1M17 17.5v1M2 13h1M21 13h1M7 9v5M12 9v5M17 9v5"/><rect x="2" y="4" width="20" height="14" rx="2"/></svg>
        <span>Yakın</span>
    </div>
    <div class="tab" data-t="kesfet">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
        <span>Keşfet</span>
    </div>
</div>

<div id="toast" class="toast">Mesaj</div>

<div id="aktarmaModal" class="modal-overlay">
    <div class="modal-content">
        <h3 style="margin-bottom:20px;color:var(--text);font-weight:800;font-size:22px;display:flex;align-items:center;gap:10px">🔄 Aktarma Kuralları</h3>
        <div style="font-size:15px;color:var(--text);line-height:1.6;">
            <div style="padding:16px;background:var(--bg-hover);border-radius:16px;margin-bottom:16px;border:1px solid var(--border)">
                <h4 style="color:var(--accent);font-weight:800;margin-bottom:8px;">1 saat içinde yapılan:</h4>
                <ul style="color:var(--text-muted);padding-left:24px;margin:0;font-weight:600">
                    <li>Otobüs → Otobüs</li>
                    <li>Otobüs → Hafif Raylı Sistem</li>
                    <li>Hafif Raylı Sistem → Otobüs</li>
                </ul>
                <p style="margin-top:12px;font-weight:800;color:var(--text)">Aktarmalar ÜCRETSİZDİR.</p>
            </div>
            <button onclick="document.getElementById('aktarmaModal').style.display='none'" class="bk" style="margin:0">Kapat</button>
        </div>
    </div>
</div>

<div id="infoModal" class="modal-overlay">
    <div class="modal-content" style="text-align:center;">
        <h3 style="color:var(--accent);margin-bottom:16px;font-weight:800;font-size:20px">⚠️ Önemli Bilgilendirme</h3>
        <p style="font-size:15px;color:var(--text);margin-bottom:12px;font-weight:600">Bu uygulama Turan KAYA tarafından geliştirilen, bağımsız bir projedir.</p>
        <p style="font-size:13px;color:var(--text-muted);margin-bottom:24px;font-weight:500">Gösterilen fiyatlar, sefer saatleri ve araç konumları tahmini veya gecikmiş olabilir.</p>
        <div style="display:flex;align-items:center;justify-content:space-between;margin-top:16px;">
            <label style="font-size:13px;color:var(--text-muted);display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:600"><input type="checkbox" id="chkGosterme" style="width:16px;height:16px;accent-color:var(--accent)" onchange="if(this.checked) localStorage.setItem('hideInfoModal','true'); else localStorage.removeItem('hideInfoModal')"> Bir daha gösterme</label>
            <button onclick="closeInfoModal()" class="bk" style="width:auto;margin:0;background:var(--accent);color:#fff;border:none">Anladım</button>
        </div>
    </div>
</div>

<div id="cerezBanner" style="display:none;position:fixed;bottom:90px;left:50%;transform:translateX(-50%);width:90%;max-width:500px;z-index:9998;background:var(--bg-panel);border:1px solid var(--border);border-radius:24px;padding:20px;box-shadow:0 12px 40px rgba(0,0,0,0.4);backdrop-filter:blur(20px);flex-direction:column;gap:16px">
  <div style="font-size:14px;color:var(--text);line-height:1.6;font-weight:500">🍪 Bu uygulama yalnızca temel işlevsellik için <strong>localStorage</strong> kullanır.</div>
  <div style="display:flex;gap:12px;width:100%">
    <button onclick="cerezReddet()" class="bk" style="margin:0;flex:1;">Sadece Zorunlu</button>
    <button onclick="cerezKabul()" class="bk" style="margin:0;flex:1;background:var(--accent);color:#fff;border:none">Kabul Et</button>
  </div>
</div>

<script src="/static/leaflet.js"></script>
<script>
"""

with open(r"c:\Users\mete2\OneDrive\Masaüstü\test\test.js", "r", encoding="utf-8") as f:
    js_content = f.read()

html_bottom = """
</script>
</body>
</html>
"""

with open(r"c:\Users\mete2\OneDrive\Masaüstü\test\test.html", "w", encoding="utf-8") as f:
    f.write(html_top + js_content + html_bottom)
print("Succesfully compiled test.html with Lovable styling.")

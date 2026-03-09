import { useState, useEffect } from "react";

/* ── SAMSUNUM-1 Banner ─────────────────────────────────────────────────────── */
export const SamsuNum1Banner = () => (
  <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 mb-4">
    <p className="text-sm font-bold text-amber-700 dark:text-amber-400 mb-2">⚠️ DEĞERLİ YOLCULARIMIZIN DİKKATİNE!</p>
    <p className="text-xs text-amber-700/80 dark:text-amber-400/80 leading-relaxed mb-2">
      Hava koşullarına bağlı olarak sefer saatlerinde değişiklik olabilir. Lütfen hareket etmeden önce güncel bilgileri kontrol edin.
    </p>
    <div className="flex flex-col gap-1 text-xs text-foreground">
      <span>⏱ Sefer Süresi: <strong>1 saat 15 dakika</strong></span>
      <span>💰 Ücret: <strong>Tam 250 TL</strong> / <strong>Öğrenci 200 TL</strong></span>
      <span>📞 <a href="tel:03624311012" className="text-primary hover:underline">0362 431 10 12</a></span>
    </div>
  </div>
);

/* ── SAMSUNUM-2 Banner ─────────────────────────────────────────────────────── */
export const SamsuNum2Banner = () => (
  <div className="rounded-xl border border-destructive/20 bg-destructive/10 p-4 mb-4">
    <p className="text-sm font-bold text-destructive mb-2">🛑 ÇALIŞMAMAKTADIR</p>
    <p className="text-xs text-destructive/80 leading-relaxed">
      DSİ Bölge Müdürlüğü çalışmalarından dolayı Samsunum-2 Gemisi çalışamamaktadır.
    </p>
  </div>
);

/* ── SAMSUNUM-3 Banner ─────────────────────────────────────────────────────── */
export const SamsuNum3Banner = () => (
  <div className="rounded-xl border border-blue-500/20 bg-blue-500/10 p-4 mb-4">
    <p className="text-sm font-bold text-blue-700 dark:text-blue-400 mb-2">ℹ️ Sefer Bilgisi</p>
    <p className="text-xs text-blue-700/80 dark:text-blue-400/80 leading-relaxed mb-2">
      Sefer saatleri doluluğa göre belirlenmektedir.
    </p>
    <div className="flex flex-col gap-1 text-xs text-foreground">
      <span>⏱ Sefer Süresi: <strong>1 saat 15 dk</strong></span>
      <span>💰 Ücret: <strong>Tam 250 TL</strong> / <strong>Öğrenci 200 TL</strong></span>
    </div>
  </div>
);

/* ── Altınkaya Feribot Banner ──────────────────────────────────────────────── */
export const FerryBanner = () => (
  <div className="rounded-xl border border-border bg-accent/50 p-4 mb-4">
    <p className="text-sm font-bold text-foreground mb-3">⛴️ Altınkaya 55 Feribot Tarifesi</p>
    <table className="w-full text-xs">
      <thead>
        <tr className="border-b border-border">
          <th className="text-left py-1.5 text-muted-foreground font-medium">Tür</th>
          <th className="text-right py-1.5 text-muted-foreground font-medium">Ücret</th>
        </tr>
      </thead>
      <tbody className="text-foreground">
        <tr className="border-b border-border/50"><td className="py-1.5">Yolcu (Tam)</td><td className="text-right font-mono">15 TL</td></tr>
        <tr className="border-b border-border/50"><td className="py-1.5">Yolcu (Öğrenci)</td><td className="text-right font-mono">7 TL</td></tr>
        <tr className="border-b border-border/50"><td className="py-1.5">Otomobil / Minibüs</td><td className="text-right font-mono">75 TL</td></tr>
        <tr className="border-b border-border/50"><td className="py-1.5">Römorklu Traktör / Kamyonet</td><td className="text-right font-mono">90 TL</td></tr>
        <tr className="border-b border-border/50"><td className="py-1.5">Kamyon (Boş)</td><td className="text-right font-mono">290 TL</td></tr>
        <tr className="border-b border-border/50"><td className="py-1.5">Kamyon (Dolu)</td><td className="text-right font-mono">580 TL</td></tr>
        <tr className="border-b border-border/50"><td className="py-1.5">Otobüs</td><td className="text-right font-mono">290 TL</td></tr>
        <tr><td className="py-1.5">Otobüs (10m üstü)</td><td className="text-right font-mono">410 TL</td></tr>
      </tbody>
    </table>
    <p className="text-[10px] text-muted-foreground mt-2">** Gece tarifesi %50 zamlıdır.</p>
  </div>
);

/* ── Teleferik Banner ──────────────────────────────────────────────────────── */
export const TeleferikBanner = () => (
  <div className="rounded-xl border border-pink-500/20 bg-pink-500/10 p-4 mb-4">
    <p className="text-sm font-bold text-pink-700 dark:text-pink-400 mb-2">🚡 Batıpark - Amisos Tepesi</p>
    <p className="text-xs text-pink-700/80 dark:text-pink-400/80 leading-relaxed mb-2">
      323 metre uzunluğundaki hat, Batı Park ile Baruthane Tümülüsleri arasında hizmet vermektedir.
    </p>
    <div className="flex flex-col gap-1 text-xs text-foreground">
      <span>🕐 Çalışma: <strong>10:30 - 22:00</strong></span>
      <span>💰 Ücret: <strong>Tam 50 TL</strong> / <strong>Öğrenci 30 TL</strong></span>
      <span>📞 <a href="tel:03624311012" className="text-primary hover:underline">0362 431 10 12</a></span>
    </div>
  </div>
);

/* ── Tramvay Tarife Banner ─────────────────────────────────────────────────── */
const weekdayData = [
  ["06:15", "07:00", "14 dk", "16 dk"],
  ["07:30", "08:00", "5 dk", "8 dk"],
  ["08:00", "09:00", "8 dk", "10 dk"],
  ["09:00", "17:00", "7 dk", "12-14 dk"],
  ["17:30", "18:30", "14 dk", "14 dk"],
  ["20:00", "21:00", "16 dk", "16 dk"],
  ["21:00", "23:30", "20 dk", "20 dk"],
];

const saturdayData = [
  ["06:15", "07:30", "16 dk"],
  ["07:30", "12:00", "16 dk"],
  ["12:00", "18:00", "12 dk"],
  ["18:00", "20:00", "14 dk"],
  ["20:30", "23:00", "20 dk"],
  ["23:00", "23:45", "30 dk"],
];

const sundayData = [
  ["06:15", "11:30", "18 dk"],
  ["11:30", "18:00", "14 dk"],
  ["18:00", "22:00", "16 dk"],
  ["22:00", "23:00", "20 dk"],
  ["23:00", "23:45", "30 dk"],
];

export const TramvayScheduleBanner = () => {
  const [tab, setTab] = useState<"haftaici" | "cumartesi" | "pazar">("haftaici");

  const tabs = [
    { id: "haftaici" as const, label: "Hafta İçi" },
    { id: "cumartesi" as const, label: "Cumartesi" },
    { id: "pazar" as const, label: "Pazar" },
  ];

  return (
    <div className="rounded-xl border border-border bg-accent/30 p-4 mb-4">
      <p className="text-sm font-bold text-foreground mb-3">🚃 Tramvay Sefer Saatleri</p>

      <div className="flex gap-1 mb-3">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex-1 rounded-lg py-1.5 text-xs font-medium transition-colors ${tab === t.id
              ? "bg-primary text-primary-foreground"
              : "bg-accent text-muted-foreground"
              }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "haftaici" && (
        <table className="w-full text-[10px]">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-1 text-muted-foreground">Başlangıç</th>
              <th className="text-left py-1 text-muted-foreground">Bitiş</th>
              <th className="text-left py-1 text-muted-foreground">Yurtlar→Tek.</th>
              <th className="text-left py-1 text-muted-foreground">Tek.→Yurtlar</th>
            </tr>
          </thead>
          <tbody>
            {weekdayData.map((row, i) => (
              <tr key={i} className="border-b border-border/30">
                <td className="py-1 font-mono text-foreground">{row[0]}</td>
                <td className="py-1 font-mono text-foreground">{row[1]}</td>
                <td className="py-1 text-foreground">{row[2]}</td>
                <td className="py-1 text-foreground">{row[3]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {tab === "cumartesi" && (
        <table className="w-full text-[10px]">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-1 text-muted-foreground">Başlangıç</th>
              <th className="text-left py-1 text-muted-foreground">Bitiş</th>
              <th className="text-left py-1 text-muted-foreground">Sıklık</th>
            </tr>
          </thead>
          <tbody>
            {saturdayData.map((row, i) => (
              <tr key={i} className="border-b border-border/30">
                <td className="py-1 font-mono text-foreground">{row[0]}</td>
                <td className="py-1 font-mono text-foreground">{row[1]}</td>
                <td className="py-1 text-foreground">{row[2]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {tab === "pazar" && (
        <table className="w-full text-[10px]">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left py-1 text-muted-foreground">Başlangıç</th>
              <th className="text-left py-1 text-muted-foreground">Bitiş</th>
              <th className="text-left py-1 text-muted-foreground">Sıklık</th>
            </tr>
          </thead>
          <tbody>
            {sundayData.map((row, i) => (
              <tr key={i} className="border-b border-border/30">
                <td className="py-1 font-mono text-foreground">{row[0]}</td>
                <td className="py-1 font-mono text-foreground">{row[1]}</td>
                <td className="py-1 text-foreground">{row[2]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

export const SamairScheduleBanner = ({ lineCode }: { lineCode: string }) => {
  const [schedule, setSchedule] = useState<any[]>([]);

  useEffect(() => {
    import("@/lib/api").then(({ fetchSamairSchedule }) => {
      fetchSamairSchedule(lineCode).then((data) => {
        if (data?.data) setSchedule(data.data || []);
        else if (Array.isArray(data)) setSchedule(data);
      });
    });
  }, [lineCode]);

  if (!schedule.length) return null;

  return (
    <div className="rounded-xl border border-border bg-accent/30 p-4 mb-4">
      <p className="text-sm font-bold text-foreground mb-3">✈️ Uçuş & Servis Saatleri</p>
      <div className="flex flex-col gap-2 max-h-48 overflow-y-auto pr-1">
        {schedule.map((s, i) => (
          <div key={i} className="flex justify-between items-center text-xs border-b border-border/50 pb-2 last:border-0 last:pb-0">
            <div className="flex flex-col">
              <span className="font-bold">{s.saat || s.kalkis} → {s.varis || s.varis_saati}</span>
              <span className="text-muted-foreground text-[10px]">{s.tarih || s.gun_format}</span>
            </div>
            <div className="text-right text-[10px] text-muted-foreground w-3/5 truncate">
              {s.firma || s.ucak_firmasi} - {s.ucak_saat || s.ucak_saatleri}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

/* ── getSpecialInfo helper ─────────────────────────────────────────────────── */
export const getSpecialInfo = (line: import("@/data/mockData").TransitLine) => {
  if (!line || !line.name) return null;
  const hatAdi = line.name.toUpperCase();
  if (hatAdi.includes("SAMSUNUM-1")) return <SamsuNum1Banner />;
  if (hatAdi.includes("SAMSUNUM-2")) return <SamsuNum2Banner />;
  if (hatAdi.includes("SAMSUNUM-3")) return <SamsuNum3Banner />;
  if (hatAdi.includes("ALTINKAYa") || hatAdi.includes("ALTINKAYA") || hatAdi.includes("FERİBOT") || hatAdi.includes("FERIBOT")) return <FerryBanner />;
  if (hatAdi.includes("TELEFERİK") || hatAdi.includes("TELEFERIK") || hatAdi.includes("Teleferik") || line.type === 'teleferik') return <TeleferikBanner />;
  if (hatAdi.includes("TRAMVAY") || hatAdi.includes("Tramvay") || line.type === 'tramvay') return <TramvayScheduleBanner />;
  if (line.type === "samair") return <SamairScheduleBanner lineCode={line.code} />;
  return null;
};

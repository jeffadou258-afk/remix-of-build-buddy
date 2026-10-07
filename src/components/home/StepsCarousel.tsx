import { useCallback, useEffect, useRef, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

export const SLIDES = [
  { n: "01", title: "Imaginez", sub: "Votre projet prend vie", img: "/constructionagent/imaginez.webp", alt: "Futur propriétaire contemplant son terrain au coucher du soleil" },
  { n: "02", title: "Concevez", sub: "Des plans sur mesure", img: "/constructionagent/concevez.webp", alt: "Architecte présentant des plans et une maquette à une cliente" },
  { n: "03", title: "Visualisez", sub: "En 3D réaliste", img: "/constructionagent/visualisez.webp", alt: "Rendu d'une villa contemporaine avec piscine au crépuscule" },
  { n: "04", title: "Construisez", sub: "Avec confiance", img: "/constructionagent/construisez.webp", alt: "Chantier d'une villa R+1 avec échafaudages et ouvriers" },
  { n: "05", title: "Réalisez", sub: "Votre vision", img: "/constructionagent/realisez.webp", alt: "Villa achevée illuminée à la tombée de la nuit" },
] as const;

const DELAY = 6000;

export function StepsCarousel() {
  const [i, setI] = useState(0);
  const [paused, setPaused] = useState(false);
  const touch = useRef<number | null>(null);
  const n = SLIDES.length;
  const go = useCallback((k: number) => setI(((k % n) + n) % n), [n]);

  useEffect(() => {
    if (paused) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const t = window.setTimeout(() => go(i + 1), DELAY);
    return () => window.clearTimeout(t);
  }, [i, paused, go]);

  const s = SLIDES[i] ?? SLIDES[0];
  return (
    <section
      aria-roledescription="carrousel"
      aria-label="Les étapes de votre projet"
      className="relative bg-foreground text-on-image"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onTouchStart={(e) => { touch.current = e.touches[0]?.clientX ?? null; setPaused(true); }}
      onTouchEnd={(e) => {
        const start = touch.current; touch.current = null; setPaused(false);
        if (start == null) return;
        const dx = (e.changedTouches[0]?.clientX ?? start) - start;
        if (Math.abs(dx) > 40) go(dx < 0 ? i + 1 : i - 1);
      }}
      onKeyDown={(e) => { if (e.key === "ArrowRight") go(i + 1); if (e.key === "ArrowLeft") go(i - 1); }}
    >
      <div className="relative h-[78vh] min-h-[480px] overflow-hidden md:h-[86vh]">
        {SLIDES.map((sl, k) => (
          <img
            key={sl.n}
            src={sl.img}
            alt={sl.alt}
            loading={k === 0 ? "eager" : "lazy"}
            decoding="async"
            aria-hidden={k !== i}
            className={`absolute inset-0 h-full w-full object-cover transition-[opacity,transform] duration-[1400ms] ease-[cubic-bezier(0.2,0.7,0.2,1)] ${k === i ? "translate-x-0 scale-100 opacity-100" : `${k < i ? "-translate-x-6" : "translate-x-6"} scale-[1.04] opacity-0`}`}
          />
        ))}
        <div className="shade-bottom absolute inset-0" />

        <div className="absolute inset-x-0 bottom-0 mx-auto max-w-7xl px-5 pb-36 md:px-8 md:pb-44" aria-live="polite">
          <div key={s.n} className="luxe-rise">
            <p className="text-xs tracking-[0.35em] text-champagne">{s.n} — ÉTAPE</p>
            <h2 className="mt-3 text-5xl md:text-7xl">{s.title}</h2>
            <p className="mt-2 text-lg opacity-85 md:text-xl">{s.sub}</p>
          </div>
        </div>

        <div className="absolute right-5 top-8 flex items-center gap-4 md:right-8 md:top-10">
          <span className="text-sm tabular-nums tracking-widest">
            <span className="text-champagne">{s.n}</span> / {String(n).padStart(2, "0")}
          </span>
          <button aria-label="Étape précédente" onClick={() => go(i - 1)} className="grid h-11 w-11 place-items-center rounded-full border border-on-image/40 transition-colors hover:bg-on-image hover:text-foreground">
            <ChevronLeft className="h-5 w-5" />
          </button>
          <button aria-label="Étape suivante" onClick={() => go(i + 1)} className="grid h-11 w-11 place-items-center rounded-full border border-on-image/40 transition-colors hover:bg-on-image hover:text-foreground">
            <ChevronRight className="h-5 w-5" />
          </button>
        </div>
      </div>

      <div className="absolute inset-x-0 bottom-0">
        <div className="mx-auto flex max-w-7xl snap-x gap-3 overflow-x-auto px-5 pb-6 md:grid md:grid-cols-5 md:overflow-visible md:px-8 md:pb-8" role="tablist">
          {SLIDES.map((sl, k) => (
            <button
              key={sl.n}
              role="tab"
              aria-selected={k === i}
              aria-label={`${sl.n} ${sl.title}`}
              onClick={() => go(k)}
              className={`group relative h-20 w-36 shrink-0 snap-start overflow-hidden text-left transition-opacity md:h-24 md:w-auto ${k === i ? "opacity-100" : "opacity-55 hover:opacity-90"}`}
            >
              <img src={sl.img} alt="" loading="lazy" decoding="async" className="absolute inset-0 h-full w-full object-cover" />
              <span className="shade-bottom absolute inset-0" />
              <span className={`absolute inset-x-0 top-0 h-0.5 bg-champagne transition-transform duration-500 origin-left ${k === i ? "scale-x-100" : "scale-x-0"}`} />
              <span className="absolute bottom-2 left-3 text-xs tracking-widest">
                <span className="text-champagne">{sl.n}</span> {sl.title}
              </span>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}

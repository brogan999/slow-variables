"use client";

import { useEffect } from "react";

// The site's one chart island. Any element with `data-tip` shows its text on hover or focus; inside a `data-marks`
// group, arrows, Home and End move focus mark to mark (one tab stop per group), Enter follows the link, Escape hides.
// The tip is aria-hidden: each mark's aria-label already says the same thing.
export function HoverLayer() {
  useEffect(() => {
    const tip = document.createElement("div");
    tip.className = "hover-tip";
    tip.setAttribute("aria-hidden", "true");
    tip.hidden = true;
    document.body.appendChild(tip);
    // with JavaScript on, each chart is one tab stop and this layer draws the tip, so the no-script fallbacks go
    document.querySelectorAll("[data-tip] > title").forEach((t) => t.remove());
    document.querySelectorAll("[data-marks]").forEach((g) => {
      const marks = Array.from(g.querySelectorAll("[data-tip]"));
      const stop = marks.find((m) => m.hasAttribute("data-stop")) ?? marks[0];
      marks.forEach((m) => m.setAttribute("tabindex", m === stop ? "0" : "-1"));
    });

    const show = (el: Element) => {
      tip.textContent = el.getAttribute("data-tip");
      tip.hidden = false;
      const r = el.getBoundingClientRect();
      const left = Math.min(Math.max(8, r.left + r.width / 2 - tip.offsetWidth / 2), innerWidth - tip.offsetWidth - 8);
      const above = r.top - tip.offsetHeight - 6;
      tip.style.left = `${left + scrollX}px`;
      tip.style.top = `${(above < 8 ? r.bottom + 6 : above) + scrollY}px`;
    };
    const hide = () => { tip.hidden = true; };
    const target = (e: Event) => (e.target instanceof Element ? e.target.closest("[data-tip]") : null);
    const over = (e: Event) => { const el = target(e); if (el) show(el); else hide(); };
    const keys = (e: KeyboardEvent) => {
      if (e.key === "Escape") return hide();
      const el = target(e);
      const marks = el?.closest("[data-marks]")?.querySelectorAll<SVGElement | HTMLElement>("[data-tip]");
      if (!el || !marks) return;
      const all = Array.from(marks);
      const i = all.indexOf(el as SVGElement);
      const to = { ArrowRight: i + 1, ArrowDown: i + 1, ArrowLeft: i - 1, ArrowUp: i - 1, Home: 0, End: all.length - 1 }[e.key];
      if (to === undefined) return;
      e.preventDefault();
      const next = all[Math.min(Math.max(to, 0), all.length - 1)];
      el.setAttribute("tabindex", "-1");
      next.setAttribute("tabindex", "0");
      next.focus();
    };
    // a link into a closed disclosure (a chart dot's derived row, a strip span's reason) opens it
    const reveal = () => {
      let d = location.hash ? document.getElementById(decodeURIComponent(location.hash.slice(1)))?.closest("details") : null;
      for (; d; d = d.parentElement?.closest("details")) d.open = true;
    };
    reveal();
    addEventListener("hashchange", reveal);
    document.addEventListener("pointerover", over);
    document.addEventListener("focusin", over);
    document.addEventListener("keydown", keys);
    addEventListener("scroll", hide, { passive: true });
    return () => {
      document.removeEventListener("pointerover", over);
      document.removeEventListener("focusin", over);
      document.removeEventListener("keydown", keys);
      removeEventListener("scroll", hide);
      removeEventListener("hashchange", reveal);
      tip.remove();
    };
  }, []);
  return null;
}

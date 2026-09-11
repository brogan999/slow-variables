"use client";

import { MoonIcon, SunIcon } from "lucide-react";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";

function set(dark: boolean) {
  const r = document.documentElement;
  r.classList.toggle("dark", dark);
  r.style.colorScheme = dark ? "dark" : "light";
  try { localStorage.theme = dark ? "dark" : "light"; } catch {}
}

// Two statically labelled buttons switched by CSS: no hydration mismatch, no state. System is followed until the first click.
export function ThemeToggle() {
  useEffect(() => {
    try { if (localStorage.theme) return; } catch { return; }
    const m = matchMedia("(prefers-color-scheme: dark)");
    const f = (e: MediaQueryListEvent) => { document.documentElement.classList.toggle("dark", e.matches); document.documentElement.style.colorScheme = e.matches ? "dark" : "light"; };
    m.addEventListener("change", f);
    return () => m.removeEventListener("change", f);
  }, []);
  return (
    <>
      <Button variant="ghost" size="icon" aria-label="Switch to dark theme" className="dark:hidden" onClick={() => set(true)}><MoonIcon aria-hidden /></Button>
      <Button variant="ghost" size="icon" aria-label="Switch to light theme" className="hidden dark:inline-flex" onClick={() => set(false)}><SunIcon aria-hidden /></Button>
    </>
  );
}

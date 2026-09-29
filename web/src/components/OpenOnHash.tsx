"use client";

import { useEffect } from "react";

/** A link to an anchor inside a folded section opens the section, so no link lands on nothing visible. */
export function OpenOnHash() {
  useEffect(() => {
    const open = () => {
      const id = decodeURIComponent(window.location.hash.slice(1));
      const el = id ? document.getElementById(id) : null;
      if (!el) return;
      let d = el.closest("details");
      if (!d?.open && d) {
        while (d) {
          d.open = true;
          d = d.parentElement?.closest("details") ?? null;
        }
        el.scrollIntoView();
      }
    };
    open();
    window.addEventListener("hashchange", open);
    return () => window.removeEventListener("hashchange", open);
  }, []);
  return null;
}

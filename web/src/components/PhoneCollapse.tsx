"use client";

import { useEffect, useRef } from "react";

// Open on desktop, folded on a phone: a long profile shows its name and summary line until tapped.
export function PhoneCollapse({ summary, children }: { summary: React.ReactNode; children: React.ReactNode }) {
  const ref = useRef<HTMLDetailsElement>(null);
  useEffect(() => { if (ref.current && window.matchMedia("(max-width: 767px)").matches) ref.current.open = false; }, []);
  return (
    <details ref={ref} open className="group">
      <summary className="cursor-pointer list-none md:pointer-events-none">{summary}<span className="md:hidden text-xs text-muted group-open:hidden"> Show the profile</span></summary>
      {children}
    </details>
  );
}

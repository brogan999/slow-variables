"use client";

import { useEffect, useState } from "react";

// The footer date is the build's generated_at; the warning appears only in the viewer's browser once it is old.
export function Freshness({ generatedAt }: { generatedAt: string }) {
  const [days, setDays] = useState<number | null>(null);
  useEffect(() => { setDays(Math.floor((Date.now() - Date.parse(generatedAt)) / 86400e3)); }, [generatedAt]);
  const stamp = generatedAt.slice(0, 16).replace("T", " ") + " UTC";
  return (
    <span>
      Data generated {stamp}.
      {days !== null && days > 3 ? <span className="text-slow"> Last update {days} days ago; the nightly job may have stalled.</span> : null}
    </span>
  );
}

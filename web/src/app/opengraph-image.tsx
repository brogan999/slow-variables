import { ImageResponse } from "next/og";
import { diffusion } from "@/lib/data";
import { SITE } from "@/lib/site";

export const alt = SITE.name;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function Image() {
  const d = diffusion();
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", padding: 64, background: "#f9f9f7", color: "#0b0b0b", fontFamily: "system-ui, sans-serif" }}>
        <div style={{ fontSize: 44, fontWeight: 600 }}>{SITE.name}</div>
        <div style={{ fontSize: 34, lineHeight: 1.3, maxWidth: 1000, color: "#0b0b0b" }}>{d.verdict}</div>
        <div style={{ fontSize: 24, color: "#52514e" }}>{SITE.description}</div>
      </div>
    ),
    size,
  );
}

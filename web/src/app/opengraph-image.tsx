import { readFileSync } from "node:fs";
import path from "node:path";
import { ImageResponse } from "next/og";
import { diffusion, index, meta } from "@/lib/data";
import { SITE } from "@/lib/site";
import { TOKENS } from "@/lib/tokens";

export const alt = SITE.name;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// The one surface that cannot read CSS variables: light tokens mirrored from globals.css, the serif loaded from disk.
export default function Image() {
  const d = diffusion();
  const published = index().indicators.filter((i) => i.published).length;
  const serif = readFileSync(path.join(process.cwd(), "src/app/fonts/InstrumentSerif-Regular.ttf"));
  const italic = readFileSync(path.join(process.cwd(), "src/app/fonts/InstrumentSerif-Italic.ttf"));
  const verdict = d.verdict.replace(/^As of \d{4}-\d{2}-\d{2}: /, "");
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", padding: 64, background: TOKENS.background, color: TOKENS.ink, fontFamily: "Instrument Serif" }}>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: 20, letterSpacing: 2, color: TOKENS.muted }}>{`A PUBLIC TRACKER · GENERATED ${meta().generated_at.slice(0, 10)}`}</div>
          <div style={{ fontSize: 96, lineHeight: 1, marginTop: 12, letterSpacing: -2 }}>{SITE.name}</div>
        </div>
        <div style={{ fontSize: 34, lineHeight: 1.25, maxWidth: 1040, fontStyle: "italic", color: TOKENS.ink }}>{verdict.charAt(0).toUpperCase() + verdict.slice(1)}</div>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 22, color: TOKENS.ink2 }}>
          <span>{`${published} indicators · every number traced to a dated, graded observation`}</span>
          <span>{SITE.url.replace(/^https?:\/\//, "")}</span>
        </div>
      </div>
    ),
    { ...size, fonts: [{ name: "Instrument Serif", data: serif, style: "normal", weight: 400 }, { name: "Instrument Serif", data: italic, style: "italic", weight: 400 }] },
  );
}

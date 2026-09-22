import { readFileSync } from "node:fs";
import path from "node:path";
import { ImageResponse } from "next/og";
import { diffusion, meta } from "@/lib/data";
import { SITE } from "@/lib/site";
import { TOKENS } from "@/lib/tokens";

export const alt = SITE.name;
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// The one surface that cannot read CSS variables: tokens mirrored from globals.css, static fonts loaded from disk.
export default function Image() {
  const d = diffusion();
  const m = meta();
  const font = (f: string) => readFileSync(path.join(process.cwd(), "src/app/fonts", f));
  const verdict = d.verdict.replace(/^As of \d{4}-\d{2}-\d{2}: /, "");
  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", flexDirection: "column", justifyContent: "space-between", padding: 64, background: TOKENS.background, color: TOKENS.ink, fontFamily: "Archivo" }}>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontFamily: "Plex Mono", fontSize: 20, letterSpacing: 3, color: TOKENS.muted }}>{`A PUBLIC TRACKER · GENERATED ${m.generated_at.slice(0, 10)}`}</div>
          <div style={{ fontSize: 96, lineHeight: 1, marginTop: 16, letterSpacing: -3 }}>{SITE.name}</div>
        </div>
        <div style={{ display: "flex", borderLeft: `4px solid ${TOKENS.ink}`, paddingLeft: 28, fontFamily: "Newsreader", fontStyle: "italic", fontSize: 36, lineHeight: 1.25, maxWidth: 1040 }}>{verdict.charAt(0).toUpperCase() + verdict.slice(1)}</div>
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "Plex Mono", fontSize: 21, color: TOKENS.ink2 }}>
          <span>{`${m.indicators_published} indicators · every number traced to a dated, graded observation`}</span>
          <span>{SITE.url.replace(/^https?:\/\//, "")}</span>
        </div>
      </div>
    ),
    {
      ...size,
      fonts: [
        { name: "Archivo", data: font("Archivo-Bold.woff"), style: "normal", weight: 700 },
        { name: "Newsreader", data: font("Newsreader-Italic.woff"), style: "italic", weight: 400 },
        { name: "Plex Mono", data: font("IBMPlexMono-Medium.woff"), style: "normal", weight: 500 },
      ],
    },
  );
}

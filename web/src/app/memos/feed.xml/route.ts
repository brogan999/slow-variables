import { memos } from "@/lib/data";
import { SITE } from "@/lib/site";

export const dynamic = "force-static"; // rendered at build from the committed memo index; no runtime file reads

const esc = (s: string) => s.replace(/[<>&'"]/g, (c) => `&#${c.charCodeAt(0)};`);

export function GET() {
  const items = [...memos()]
    .reverse()
    .map((m) => {
      const url = `${SITE.url}/memos/${m.date}`;
      return `<item><title>${esc(m.title)}</title><link>${url}</link><guid isPermaLink="true">${url}</guid><pubDate>${new Date(`${m.date}T09:17:00Z`).toUTCString()}</pubDate><description>${esc(m.summary ?? "")}</description></item>`;
    })
    .join("");
  const xml = `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>${esc(SITE.name)} weekly memos</title><link>${SITE.url}/memos</link><description>${esc(SITE.description)}</description><language>en</language>${items}</channel></rss>`;
  return new Response(xml, { headers: { "Content-Type": "application/rss+xml; charset=utf-8" } });
}

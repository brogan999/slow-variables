import type { MetadataRoute } from "next";
import { index, memos, meta, seriesKeys } from "@/lib/data";
import { SITE } from "@/lib/site";

const STATIC = ["", "/capture", "/memos", "/query", "/stack", "/indicators", "/predictions", "/compare", "/bottlenecks", "/ledger", "/crosswalk", "/sources", "/methodology", "/changelog"];

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date(meta().generated_at);
  const { indicators, buckets, layers } = index();
  const url = (p: string) => `${SITE.url}${p}`;
  return [
    ...STATIC.map((p) => ({ url: url(p), lastModified, changeFrequency: "daily" as const, priority: p === "" ? 1 : 0.8 })),
    ...memos().map((m) => ({ url: url(`/memos/${m.date}`), lastModified, changeFrequency: "weekly" as const, priority: 0.7 })),
    ...buckets.map((b) => ({ url: url(`/buckets/${b.id}`), lastModified, changeFrequency: "daily" as const, priority: 0.7 })),
    ...layers.map((l) => ({ url: url(`/layers/${l.id}`), lastModified, changeFrequency: "daily" as const, priority: 0.7 })),
    ...indicators.filter((i) => i.published).map((i) => ({ url: url(`/indicators/${i.id}`), lastModified, changeFrequency: "daily" as const, priority: 0.6 })),
    ...seriesKeys().map((k) => ({ url: url(`/series/${k}`), lastModified, changeFrequency: "weekly" as const, priority: 0.3 })),
  ];
}

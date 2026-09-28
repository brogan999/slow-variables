import type { MetadataRoute } from "next";
import { atlas, census, futures, index, meta, seriesKeys } from "@/lib/data";
import { EVIDENCE, STOPS } from "@/lib/nav";
import { SITE } from "@/lib/site";

const STATIC = ["", ...STOPS.map((s) => s.href), ...EVIDENCE.map(([href]) => href), "/legal", "/ask"];

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = new Date(meta().generated_at);
  const { indicators, buckets, layers } = index();
  const url = (p: string) => `${SITE.url}${p}`;
  return [
    ...STATIC.map((p) => ({ url: url(p), lastModified, changeFrequency: "daily" as const, priority: p === "" ? 1 : 0.8 })),
    ...atlas().domains.map((d) => ({ url: url(`/singularity/atlas/${d.id}`), lastModified, changeFrequency: "weekly" as const, priority: 0.7 })),
    ...census().roles.map((r) => ({ url: url(r.href), lastModified, changeFrequency: "monthly" as const, priority: 0.5 })),
    ...[...futures().imagined.filter((d) => d.href).map((d) => d.href as string), ...futures().expected.map((d) => d.href), ...futures().categories.map((c) => c.href)].map((h) => ({ url: url(h), lastModified, changeFrequency: "monthly" as const, priority: 0.5 })),
    ...buckets.map((b) => ({ url: url(`/buckets/${b.id}`), lastModified, changeFrequency: "daily" as const, priority: 0.7 })),
    ...layers.map((l) => ({ url: url(`/layers/${l.id}`), lastModified, changeFrequency: "daily" as const, priority: 0.7 })),
    ...indicators.filter((i) => i.published).map((i) => ({ url: url(`/indicators/${i.id}`), lastModified, changeFrequency: "daily" as const, priority: 0.6 })),
    ...seriesKeys().map((k) => ({ url: url(`/series/${k}`), lastModified, changeFrequency: "weekly" as const, priority: 0.3 })),
  ];
}

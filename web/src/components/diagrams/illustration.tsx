// A picture made with AI image generation, shown with its credit. The file, alt text and stage are the export's
// (seed/illustrations.yaml); every file is one WebP of the size below, which `check` verifies.
export const CREDIT = "Illustration made with AI image generation; not evidence";

export function Illustration({ file, alt, stage, eager = false, className = "" }: { file: string; alt: string; stage?: "next" | "later" | null; eager?: boolean; className?: string }) {
  return (
    <figure className={`flex flex-col gap-1 ${className}`}>
      {/* eslint-disable-next-line @next/next/no-img-element -- static WebP in public/, served as written */}
      <img src={file} width={720} height={480} alt={alt} loading={eager ? "eager" : "lazy"} decoding="async" className="h-auto w-full rounded-sm" />
      <figcaption className="text-[11px] leading-snug text-muted">
        {CREDIT}.{stage ? <> It pictures this site&apos;s judgement of the {stage} stage, not anything observed.</> : null}
      </figcaption>
    </figure>
  );
}

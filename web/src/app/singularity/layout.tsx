import { Fraunces } from "next/font/google";

// Fraunces and the gold ornament are scoped to this route; the palette is the site's (globals.css, .theme-manuscript).
const fraunces = Fraunces({ subsets: ["latin"], style: ["normal", "italic"], axes: ["opsz", "SOFT"], variable: "--font-fraunces", display: "swap" });

export default function SingularityLayout({ children }: { children: React.ReactNode }) {
  return <div className={`theme-manuscript ${fraunces.variable}`}>{children}</div>;
}

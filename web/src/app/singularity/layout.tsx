import { Fraunces } from "next/font/google";

// The manuscript look is scoped to this route: globals.css keys its palette on body:has(.theme-manuscript).
const fraunces = Fraunces({ subsets: ["latin"], style: ["normal", "italic"], axes: ["opsz", "SOFT"], variable: "--font-fraunces", display: "swap" });

export default function SingularityLayout({ children }: { children: React.ReactNode }) {
  return <div className={`theme-manuscript ${fraunces.variable}`}>{children}</div>;
}

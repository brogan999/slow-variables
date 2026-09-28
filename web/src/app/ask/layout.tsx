// The Ask page wears a chat layout scoped to this route: globals.css keys it on body:has(.ask-shell).
export default function AskLayout({ children }: { children: React.ReactNode }) {
  return <div className="ask-shell flex-1 flex flex-col">{children}</div>;
}

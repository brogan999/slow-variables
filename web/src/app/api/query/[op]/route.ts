// The one route handler: a POST proxy to the query service, holding the token server-side.
export async function POST(req: Request, { params }: { params: Promise<{ op: string }> }) {
  const { op } = await params;
  if (op !== "ask" && op !== "sql") return Response.json({ error: "not found" }, { status: 404 });
  const url = process.env.QUERY_URL, token = process.env.QUERY_TOKEN;
  if (!url || !token) return Response.json({ error: "offline", detail: "query service not configured" }, { status: 503 });
  let body: unknown;
  try { body = await req.json(); } catch { return Response.json({ error: "bad json" }, { status: 400 }); }
  try {
    const r = await fetch(`${url}/${op}`, {
      method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(body), signal: AbortSignal.timeout(op === "ask" ? 60_000 : 30_000), // the Fly machine cold-starts in ~20 s
    });
    return Response.json(await r.json(), { status: r.status });
  } catch {
    return Response.json({ error: "offline", detail: "query service unreachable" }, { status: 503 });
  }
}

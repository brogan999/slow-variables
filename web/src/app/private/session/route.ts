import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import { configured, issue, verify } from "@/lib/private";

// Signing in: a form post from this site's own login page, answered with a redirect either way.
export async function POST(request: Request) {
  if (!configured()) notFound();
  const origin = request.headers.get("origin") ?? "";
  const hosts = [request.headers.get("host"), request.headers.get("x-forwarded-host")];
  if (!URL.canParse(origin) || !hosts.includes(new URL(origin).host)) return new Response(null, { status: 403 });
  const password = (await request.formData().catch(() => null))?.get("password");
  const ok = typeof password === "string" && verify(password);
  if (ok) {
    const c = issue();
    (await cookies()).set(c.name, c.value, c.options);
  }
  return new Response(null, { status: 303, headers: { Location: ok ? "/private" : "/private/login?e=1" } });
}

import "server-only";
import { createHmac, scryptSync, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

// The lock on the private area. This is the only file that reads its settings; the content it guards is in no
// build and no repository of the site's, and is fetched only after the session below has been checked.

const LIVE = Boolean(process.env.VERCEL);
// A browser refuses a __Secure- cookie over plain http, so a run on localhost uses the plain name.
const COOKIE = LIVE ? "__Secure-sv_private" : "sv_private";
const THIRTY_DAYS_S = 2_592_000;
const THIRTY_DAYS_MS = 2_592_000_000;

/** The area exists only where all four settings are present; anywhere else every address under it is not found. */
export function configured() {
  const e = process.env;
  return Boolean(e.PRIVATE_PASSWORD_HASH && e.PRIVATE_SESSION_SECRET && e.PRIVATE_CONTENT_REPO && e.PRIVATE_CONTENT_TOKEN);
}

const same = (a: Buffer, b: Buffer) => a.length === b.length && timingSafeEqual(a, b);
const sign = (expiry: string) => createHmac("sha256", process.env.PRIVATE_SESSION_SECRET ?? "").update(expiry).digest("hex");

/** True when the request carries a cookie this server signed and its expiry is still ahead. */
export async function session() {
  if (!configured()) return false;
  const [expiry, mac] = ((await cookies()).get(COOKIE)?.value ?? "").split(".");
  if (!expiry || !mac || !same(Buffer.from(mac), Buffer.from(sign(expiry)))) return false;
  return Number(expiry) > Date.now();
}

/** Checks a password against the stored "<salt hex>:<hash hex>" (scrypt, Node's default cost, as the hashing script writes it). */
export function verify(password: string) {
  const [salt, hash] = (process.env.PRIVATE_PASSWORD_HASH ?? "").split(":");
  if (!salt || !hash || !password || password.length > 1024) return false;
  const want = Buffer.from(hash, "hex");
  return same(scryptSync(password, Buffer.from(salt, "hex"), want.length), want);
}

/** A new session cookie: "<expiry in epoch milliseconds>.<HMAC-SHA256 of the expiry>". */
export function issue() {
  const expiry = String(Date.now() + THIRTY_DAYS_MS);
  return { name: COOKIE, value: `${expiry}.${sign(expiry)}`, options: { httpOnly: true, secure: LIVE, sameSite: "lax" as const, path: "/private", maxAge: THIRTY_DAYS_S } };
}

export type PrivateDoc = { slug: string; title: string; kind: "doc" | "table"; file: string };
export type PrivateSection = { slug: string; title: string; documents: PrivateDoc[] };
export type PrivateManifest = { sections: PrivateSection[] };

const cache = new Map<string, { at: number; data: unknown }>();
const KEPT_MS = 180_000;

/** One file of the bundle, or null without a session. The session is checked before anything is fetched or read
    from the cache. `path` is "manifest.json" or a file name the manifest lists, never text from the request. */
export async function load<T>(path: string): Promise<T | null> {
  if (!(await session())) return null;
  if (!/^[a-z0-9-]+\.json$/.test(path)) return null;
  const hit = cache.get(path);
  if (hit && Date.now() - hit.at < KEPT_MS) return hit.data as T;
  // a local store for testing against invented files; the live host never reads it
  const base = process.env.VERCEL ? undefined : process.env.PRIVATE_CONTENT_BASE;
  const res = base
    ? await fetch(`${base}/${path}`, { cache: "no-store" })
    : await fetch(`https://api.github.com/repos/${process.env.PRIVATE_CONTENT_REPO}/contents/${path}`, {
        headers: { Authorization: `Bearer ${process.env.PRIVATE_CONTENT_TOKEN}`, Accept: "application/vnd.github.raw+json" },
        cache: "no-store",
      });
  if (!res.ok) throw new Error("the private store did not answer");
  const data: unknown = await res.json();
  cache.set(path, { at: Date.now(), data });
  return data as T;
}

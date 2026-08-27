import { cookies } from "next/headers";

const API_BASE = process.env.API_BASE_URL || "http://localhost:8000";

// Auth.js v5 uses different cookie names in dev vs production
const SESSION_COOKIE_NAMES = [
  "authjs.session-token",           // dev (http)
  "__Secure-authjs.session-token",  // production (https)
];

async function getSessionToken(): Promise<string | null> {
  const cookieStore = await cookies();
  for (const name of SESSION_COOKIE_NAMES) {
    const cookie = cookieStore.get(name);
    if (cookie?.value) {
      return cookie.value;
    }
  }
  return null;
}

export async function apiFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  const token = await getSessionToken();
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });
}
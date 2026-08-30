import { NextRequest, NextResponse } from "next/server";

import { apiFetch } from "@/lib/api";

export async function POST(request: NextRequest) {
  const body = await request.text();
  const res = await apiFetch("/api/ratings", {
    method: "POST",
    body,
  });
  const responseBody = await res.text();
  return new NextResponse(responseBody, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  });
}
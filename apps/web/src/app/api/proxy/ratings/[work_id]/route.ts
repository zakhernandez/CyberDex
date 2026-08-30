import { NextRequest, NextResponse } from "next/server";

import { apiFetch } from "@/lib/api";

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ work_id: string }> }
) {
  const { work_id } = await params;
  const res = await apiFetch(`/api/ratings/${work_id}`, {
    method: "DELETE",
  });
  return new NextResponse(null, { status: res.status });
}
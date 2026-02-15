import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL || "http://api:8000";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ versionId: string }> }
) {
  const apiKey = request.headers.get("X-API-Key");
  const { versionId } = await params;

  try {
    const res = await fetch(`${API_BASE_URL}/admin/settings/${versionId}/activate`, {
      method: "POST",
      headers: { "X-API-Key": apiKey || "" },
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ detail: "Failed to connect to API" }, { status: 500 });
  }
}

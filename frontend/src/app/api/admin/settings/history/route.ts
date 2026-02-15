import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL || "http://api:8000";

export async function GET(request: NextRequest) {
  const apiKey = request.headers.get("X-API-Key");
  const { searchParams } = new URL(request.url);
  const limit = searchParams.get("limit") || "20";

  try {
    const res = await fetch(`${API_BASE_URL}/admin/settings/history?limit=${limit}`, {
      headers: { "X-API-Key": apiKey || "" },
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json({ detail: "Failed to connect to API" }, { status: 500 });
  }
}

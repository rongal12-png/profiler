import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.API_BASE_URL || "http://api:8000";

export async function GET() {
  try {
    const res = await fetch(`${API_BASE}/projects`);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json([], { status: 200 });
  }
}

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();
    const res = await fetch(`${API_BASE}/projects`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (e) {
    return NextResponse.json({ detail: String(e) }, { status: 500 });
  }
}

import { NextRequest, NextResponse } from "next/server";

const API_BASE_URL = process.env.API_BASE_URL || "http://api:8000";

export async function GET(request: NextRequest) {
  const apiKey = request.headers.get("X-API-Key");

  try {
    const res = await fetch(`${API_BASE_URL}/admin/settings`, {
      headers: {
        "X-API-Key": apiKey || "",
      },
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    return NextResponse.json(
      { detail: "Failed to connect to API" },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  const apiKey = request.headers.get("X-API-Key");
  const body = await request.json();

  try {
    const res = await fetch(`${API_BASE_URL}/admin/settings`, {
      method: "PUT",
      headers: {
        "X-API-Key": apiKey || "",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    return NextResponse.json(
      { detail: "Failed to connect to API" },
      { status: 500 }
    );
  }
}

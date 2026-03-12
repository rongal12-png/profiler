import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.API_BASE_URL || "http://api:8000";

export async function GET(request: NextRequest) {
  const lang = request.nextUrl.searchParams.get("lang") || "he";

  try {
    const response = await fetch(`${API_BASE}/guide/pdf?lang=${lang}`);

    if (!response.ok) {
      return NextResponse.json(
        { detail: "Failed to generate guide PDF" },
        { status: response.status }
      );
    }

    const buffer = await response.arrayBuffer();
    return new NextResponse(buffer, {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="wallet-intelligence-guide-${lang}.pdf"`,
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Failed to connect to analysis API" },
      { status: 502 }
    );
  }
}

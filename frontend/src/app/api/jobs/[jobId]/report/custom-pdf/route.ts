import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.API_BASE_URL || "http://api:8000";

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params;

  try {
    const body = await request.text();
    const response = await fetch(
      `${API_BASE}/jobs/${jobId}/report/custom-pdf`,
      {
        method: "POST",
        headers: { "Content-Type": "text/plain" },
        body,
      }
    );

    if (!response.ok) {
      return NextResponse.json(
        { detail: "PDF generation failed" },
        { status: response.status }
      );
    }

    const buffer = await response.arrayBuffer();
    return new NextResponse(buffer, {
      status: 200,
      headers: {
        "Content-Type": "application/pdf",
        "Content-Disposition": `attachment; filename="edited-report-${jobId}.pdf"`,
      },
    });
  } catch {
    return NextResponse.json(
      { detail: "Failed to connect to analysis API" },
      { status: 502 }
    );
  }
}

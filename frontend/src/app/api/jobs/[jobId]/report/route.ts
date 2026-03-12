import { NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.API_BASE_URL || "http://api:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ jobId: string }> }
) {
  const { jobId } = await params;
  const format = request.nextUrl.searchParams.get("format") || "json";

  try {
    const response = await fetch(
      `${API_BASE}/jobs/${jobId}/report?format=${format}`
    );

    const contentType =
      response.headers.get("content-type") || "application/json";

    // Handle binary responses (PDF, DOCX)
    if (format === "pdf" || format === "docx") {
      const buffer = await response.arrayBuffer();
      const ext = format === "pdf" ? "pdf" : "docx";
      const mime =
        format === "pdf"
          ? "application/pdf"
          : "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
      return new NextResponse(buffer, {
        status: response.status,
        headers: {
          "Content-Type": mime,
          "Content-Disposition": `attachment; filename="wallet-report-${jobId}.${ext}"`,
        },
      });
    }

    const body = await response.text();

    return new NextResponse(body, {
      status: response.status,
      headers: { "Content-Type": contentType },
    });
  } catch {
    return NextResponse.json(
      { detail: "Failed to connect to analysis API" },
      { status: 502 }
    );
  }
}

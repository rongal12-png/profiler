import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  try {
    const { password } = await request.json();

    // Get password from environment variable
    const correctPassword = process.env.SITE_PASSWORD || "wallet123";

    if (password === correctPassword) {
      const response = NextResponse.json({ success: true });

      // Set authentication cookie (expires in 7 days)
      response.cookies.set("authenticated", "true", {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        maxAge: 60 * 60 * 24 * 7, // 7 days
        path: "/",
      });

      return response;
    } else {
      return NextResponse.json(
        { error: "סיסמה שגויה" },
        { status: 401 }
      );
    }
  } catch (error) {
    return NextResponse.json(
      { error: "שגיאה בשרת" },
      { status: 500 }
    );
  }
}

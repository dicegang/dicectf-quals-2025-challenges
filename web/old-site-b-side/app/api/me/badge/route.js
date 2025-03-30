import { NextResponse } from "next/server"

import { getSession, getUser } from "@/users.mjs"

export async function GET() {
  const session = await getSession()
  const user = getUser(session.name)

  if (user) {
    return new NextResponse(user.badge, {
      headers: [
        ["Content-Type", "image/gif"],
        ["Content-Disposition", `attachment; filename="badge.gif"`],
      ],
      status: 200,
    })
  } else {
    return new NextResponse(null, { status: 401 })
  }
}

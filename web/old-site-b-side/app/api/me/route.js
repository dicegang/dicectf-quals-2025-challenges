import { NextResponse } from "next/server"

import { getSession, getUser } from "@/users.mjs"
import { escaped, html4 } from "@/utils.mjs"

export async function GET() {
  const session = await getSession()
  const user = getUser(session.name)

  let msg
  if (user) {
    msg = escaped`<CENTER><SPAN STYLE="vertical-align:baseline">Logged in as <FONT COLOR="yellow">${user.name}</FONT> </SPAN><IMG SRC="/api/me/badge" WIDTH="88" HEIGHT="31" STYLE="vertical-align:middle"></CENTER>`
  } else {
    msg = `<CENTER>Not logged in</CENTER>`
  }

  return new NextResponse(html4(null, msg), {
    headers: [["Content-Type", "text/html"]],
    status: 200,
  })
}

import { NextResponse } from "next/server"
import { z } from "zod"
import { zfd } from "zod-form-data"

import { getSession, getUser } from "@/users.mjs"
import { escaped, html4 } from "@/utils.mjs"

const messages = [
  "[admin] welcome to la ctf! >w<",
  "[undefined] //#sourceMappingURL=%2Fflag.txt",
  "[admin] Welcome to DiceCTF! ^-^",
]

const SCHEMA = zfd.formData({
  // we only allow ASCII text, as the 2000s intended
  "UR MESSAGE": zfd.text(z.string().min(1).max(1000).regex(/^[ -~]+$/)),
})

// aplet got really mad at me when this code got the entire ψβρ infra hacked
// so no more writing to disk >:D

export async function POST(req) {
  const parsedData = SCHEMA.safeParse(await req.formData())
  if (parsedData.success) {
    const session = await getSession()
    const user = getUser(session.name)
    if (user) {
      messages.push(`[${user.name}] ${parsedData.data["UR MESSAGE"]}`)
    }
  }
  return NextResponse.redirect(new URL("/", req.url), { status: 303 })
}

export async function GET() {
  const list = messages.map(m => escaped`<LI>${m}</LI>`).join("")
  const html = html4("arcblrost's guestbook!!!", `<UL>${list}</UL>`)
  return new NextResponse(html, {
    headers: [["Content-Type", "text/html"]],
    status: 200,
  })
}

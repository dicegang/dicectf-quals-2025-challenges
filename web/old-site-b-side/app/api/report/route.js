import { NextResponse } from "next/server"
import { z } from "zod"
import { zfd } from "zod-form-data"

import * as bot from "@/report.mjs"

const SCHEMA = zfd.formData({
  "HACKER IP": zfd.text(z.string().url()),
})
const ADMINBOT_VISIT_TIME = 15_000

let lastVisit = 0

export async function POST(req) {
  const parsedData = SCHEMA.safeParse(await req.formData())
  if (parsedData.success) {
    // debounce admin bot
    const now = (new Date()).getTime()
    const deltaTime = now - lastVisit
    if (deltaTime < ADMINBOT_VISIT_TIME) {
      const retryAfter = Math.ceil((ADMINBOT_VISIT_TIME - deltaTime) / 1000)
      return NextResponse.json(`Please slow down (wait ${retryAfter} more seconds)`, {
        headers: [["Retry-After", retryAfter]],
        status: 429,
      })
    }
    lastVisit = now

    bot.visit(parsedData.data["HACKER IP"])
    return NextResponse.json("ur hacker will be deleted soon....", { status: 200 })
  } else {
    return NextResponse.json(parsedData.error, { status: 400 })
  }
}

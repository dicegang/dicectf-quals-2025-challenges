import { imageSize } from "image-size"
import { NextResponse } from "next/server"
import { z } from "zod"
import { zfd } from "zod-form-data"

import { addUser, getSession } from "@/users.mjs"

const SCHEMA = zfd.formData({
  "UR NAME": zfd.text(z.string().min(1).max(100).regex(/^[ -~]+$/)),
  "UR EMAIL": zfd.text(z.string().min(1).max(1000).email()),
  "UR BADGE": zfd.file(),
})

export async function POST(req) {
  const parsedData = SCHEMA.safeParse(await req.formData())
  if (parsedData.success) {
    try {
      const badge = parsedData.data["UR BADGE"]
      const badgeData = new Uint8Array(await badge.arrayBuffer())
      if (badgeData.length >= 26 && badgeData.length < 1000000 && [0x47, 0x49, 0x46, 0x38].every((x, i) => x === badgeData[i])) {
          const badgeImageSize = imageSize(badgeData)
          if (badgeImageSize.width == 88 && badgeImageSize.height == 31) {
            if (addUser(parsedData.data["UR NAME"], parsedData.data["UR EMAIL"], badgeData)) {
              const session = await getSession()
              session.name = parsedData.data["UR NAME"]
              await session.save()
              return NextResponse.json(`User ${parsedData.data["UR NAME"]} registered!`, { status: 200 })
            } else {
              return NextResponse.json(`User ${parsedData.data["UR NAME"]} already taken :(`, { status: 400 })
            }
          }
      }
    } catch {}
    return NextResponse.json(`Bad badge data`, { status: 400 })
  } else {
    return NextResponse.json(parsedData.error, { status: 400 })
  }
}

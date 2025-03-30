import { getIronSession } from "iron-session"
import { cookies } from "next/headers"
import crypto from "node:crypto"
import fs from "node:fs"

export const SESSION_PASSWORD = crypto.randomBytes(64).toString("base64")

export async function getSession() {
  return getIronSession(await cookies(), {
    password: SESSION_PASSWORD,
    cookieName: "session",
  })
}

const users = new Map()

export function getUser(name) {
  return users.get(name)
}

export function addUser(name, email, badge) {
  if (users.has(name)) return false
  users.set(name, { name: name, email: email, badge: badge })
  return true
}

// prepopulate some users for flavor
const dicectf = fs.readFileSync("public/images/dicectf.gif")
const flag = new TextEncoder().encode(process.env.FLAG || "dice{fake_flag}")
const adminBadge = new Uint8Array(dicectf.length + flag.length)
adminBadge.set(dicectf, 0)
adminBadge.set(flag, dicectf.length)
addUser("admin", "noreply@ctf.dicega.ng", adminBadge)
addUser("undefined", "14c7f202-54a5-4041-88c1-e6f5f00c1791@emailhook.site", new Uint8Array())
